# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Freescale Semiconductor, Inc.
# All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
#

from oslo.config import cfg
from nscs.crdservice.openstack.common import importutils
from nscs.crdservice.openstack.common import log as logging
from nscs_firewall.crdservice.db import firewall_db
from nscs_firewall.crdservice.plugins.common import constants

from nscs.crdservice.openstack.common import context
from neutronclient.v2_0 import client as neutron_client
from nscs.crdservice.common import exceptions as q_exc
import configparser
from nscs.crdservice.openstack.common.rpc import proxy

LOG = logging.getLogger(__name__)


modconf = configparser.ConfigParser()
confpath = cfg.CONF.config_file[0]
confpath = confpath.replace('nscs.conf', 'modules/firewall.conf')
modconf.read(confpath)
nwservice_driver = str(modconf.get("DEFAULT","nwservice_driver"))


class FirewallAgentApi(proxy.RpcProxy):
    """Plugin side of plugin to agent RPC API."""

    API_VERSION = '1.0'

    def __init__(self, topic, host):
        super(FirewallAgentApi, self).__init__(topic, self.API_VERSION)
        self.host = host

    def create_firewall(self, context, firewall):
        return self.fanout_cast(
            context,
            self.make_msg('create_firewall', firewall=firewall,
                          host=self.host),
            topic=self.topic
        )

    def update_firewall(self, context, firewall):
        return self.fanout_cast(
            context,
            self.make_msg('update_firewall', firewall=firewall,
                          host=self.host),
            topic=self.topic
        )

    def delete_firewall(self, context, firewall):
        return self.fanout_cast(
            context,
            self.make_msg('delete_firewall', firewall=firewall,
                          host=self.host),
            topic=self.topic
        )

class FirewallDriver():
    """
    The Firewall Driver class
    The following tasks are done in this calss
    [1] Check for the changes in the Firewall configuration and intimates the 
        Network Services driver with the logical UUID, API and other info.
    """
    def __init__(self):
        self.db = firewall_db.Firewall_db_mixin()
        self.driver = importutils.import_object(nwservice_driver)
        self.agent_rpc = FirewallAgentApi(
            'l3_agent',
            cfg.CONF.host
        )
        
    def firewall_config_update(self,context,firewall_id,fw_with_rules):
        #LOG.debug(_("Prepare Firewall Config Update Message..."))
        self.fw_db = firewall_db.Firewall_db_mixin()
        if firewall_id:
            fw_details = self.db.get_firewall(context, firewall_id)
            if fw_details['config_handle_id']:
                config_details = self.db.get_config_handle(context, fw_details['config_handle_id'])
                if config_details:
                    config_mode = config_details['config_mode']
                    if config_mode == 'NFV':
                        self.agent_rpc.delete_firewall(context, fw_with_rules)
                        self.prepare_update(fw_details['config_handle_id'],constants.FW_UPDATE)
                    elif config_mode == 'NN':
                        self.agent_rpc.update_firewall(context, fw_with_rules)
                    elif config_mode == 'OFC':
                        #Need to handle CRD Consumer Notifier
                        pass
            else:
                self.agent_rpc.update_firewall(context, fw_with_rules)
        return
    
    def firewall_config_delete(self,context,config_handle_id,fw_with_rules):
        #LOG.debug(_("Prepare Firewall Config Delete Message..."))
        if config_handle_id:
            config_details = self.db.get_config_handle(context, config_handle_id)
            if config_details:
                config_mode = config_details['config_mode']
                if config_mode == 'NFV':
                    self.prepare_update(config_handle_id,constants.FW_UPDATE)
                elif config_mode == 'NN':
                    self.agent_rpc.delete_firewall(context, fw_with_rules)
                elif config_mode == 'OFC':
                    #Need to handle CRD Consumer Notifier
                    pass
        else:
            self.agent_rpc.delete_firewall(context, fw_with_rules)
        return
    
    def prepare_update(self,config_handle_id,method):
        #LOG.debug(_("Firewall Config Handle ID => %s"),(str(config_handle_id)))
        if config_handle_id:
            update_dict = { "header":"request",
                        "config_handle_id":config_handle_id,
                        "slug":"firewall",
                        "version":"0.0",
                      }
            #LOG.debug(_("Notification Data : %s" % str(update_dict)))
            self.send_modified_notification(config_handle_id,{'config':update_dict})
        return

    def send_modified_notification(self,config_handle_id,notify_data):
        #LOG.debug(_('Send modified notification to NS Driver: Data: %s' % str(notify_data)))
        self.driver.send_rpc_msg(config_handle_id,notify_data)

def get_service_from_catalog(catalog, service_type):
    if catalog:
        for service in catalog:
            if service['type'] == service_type:
                return service
    return None

def url_for(context, service_type, admin=False, endpoint_type=None):
    endpoint_type = endpoint_type or 'publicURL'
    catalog = context.service_catalog
    service = get_service_from_catalog(catalog, service_type)
    if service:
        try:
            if admin:
                return service['endpoints'][0]['adminURL']
            else:
                return service['endpoints'][0][endpoint_type]
        except (IndexError, KeyError):
            raise q_exc.ServiceCatalogException(service_name=str(service_type))
    else:
        raise q_exc.ServiceCatalogException(service_name=str(service_type))
        
def neutronclient(context=None):
    c = neutron_client.Client(token=context.auth_token,
                              endpoint_url=url_for(context, 'network'))
    return c
