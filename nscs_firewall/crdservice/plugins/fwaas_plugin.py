# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2013 Big Switch Networks, Inc.
# All Rights Reserved.
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
# @author: Sumit Naiksatam, sumitnaiksatam@gmail.com, Big Switch Networks, Inc.

from oslo.config import cfg

from nscs.crdservice.common import exceptions as n_exception
from nscs.crdservice.common import rpc as q_rpc
from nscs.crdservice.common import topics
from nscs.crdservice import context as crd_context
from nscs.crdservice.db import api as qdbapi
from nscs_firewall.crdservice.db import firewall_db
from nscs_firewall.crdservice.extensions import firewall as fw_ext
from nscs.crdservice.openstack.common import log as logging
from nscs.crdservice.openstack.common import rpc
from nscs.crdservice.openstack.common.rpc import proxy
from nscs_firewall.crdservice.plugins.common import constants as const
from nscs.crdservice.openstack.common import importutils
from nscs_firewall.crdservice.listener.firewall import FirewallListener
import time
import configparser
LOG = logging.getLogger(__name__)

modconf = configparser.ConfigParser()
confpath = cfg.CONF.config_file[0]
confpath = confpath.replace('nscs.conf', 'modules/firewall.conf')
modconf.read(confpath)
firewall_driver = str(modconf.get("FWDRIVER","firewall_driver"))


class FirewallPlugin(FirewallListener, firewall_db.Firewall_db_mixin):

    """Implementation of the Crd Firewall Service Plugin.

    This class manages the workflow of FWaaS request/response.
    Most DB related works are implemented in class
    firewall_db.Firewall_db_mixin.
    """
    supported_extension_aliases = ["fwaas"]

    def __init__(self):
        """Do the initialization for the firewall service plugin here."""
	self.db = firewall_db.Firewall_db_mixin()
        self.driver = importutils.import_object(firewall_driver)
        qdbapi.register_models()
	super(FirewallPlugin, self).__init__()


    def _make_firewall_dict_with_rules(self, context, firewall_id):
        firewall = self.get_firewall(context, firewall_id)
        fw_policy_id = firewall['firewall_policy_id']
        if fw_policy_id:
            fw_policy = self.get_firewall_policy(context, fw_policy_id)
            fw_rules_list = [self.get_firewall_rule(
                context, rule_id) for rule_id in fw_policy['firewall_rules']]
            firewall['firewall_rule_list'] = fw_rules_list
        else:
            firewall['firewall_rule_list'] = []
        # FIXME(Sumit): If the size of the firewall object we are creating
        # here exceeds the largest message size supported by rabbit/qpid
        # then we will have a problem.
        return firewall

    def _rpc_update_firewall(self, context, firewall_id):
        #status_update = {"firewall": {"status": const.PENDING_UPDATE}}
        status_update = {"firewall": {"status": const.ACTIVE}}
        fw = super(FirewallPlugin, self).update_firewall(context, firewall_id,
                                                         status_update)
        if fw:
            fw_with_rules = (
                self._make_firewall_dict_with_rules(context,
                                                    firewall_id))
            #self.agent_rpc.update_firewall(context, fw_with_rules)
            self.driver.firewall_config_update(context,firewall_id,fw_with_rules)
            

    def _rpc_update_firewall_policy(self, context, firewall_policy_id):
        firewall_policy = self.get_firewall_policy(context, firewall_policy_id)
        if firewall_policy:
            for firewall_id in firewall_policy['firewall_list']:
                self._rpc_update_firewall(context, firewall_id)

    def _ensure_update_firewall(self, context, firewall_id):
        fwall = self.get_firewall(context, firewall_id)
        if fwall['status'] in [const.PENDING_CREATE,
                               const.PENDING_UPDATE,
                               const.PENDING_DELETE]:
            raise fw_ext.FirewallInPendingState(firewall_id=firewall_id,
                                                pending_state=fwall['status'])

    def _ensure_update_firewall_policy(self, context, firewall_policy_id):
        firewall_policy = self.get_firewall_policy(context, firewall_policy_id)
        if firewall_policy and 'firewall_list' in firewall_policy:
            for firewall_id in firewall_policy['firewall_list']:
                self._ensure_update_firewall(context, firewall_id)

    def _ensure_update_or_delete_firewall_rule(self, context,
                                               firewall_rule_id):
        fw_rule = self.get_firewall_rule(context, firewall_rule_id)
        if 'firewall_policy_id' in fw_rule and fw_rule['firewall_policy_id']:
            self._ensure_update_firewall_policy(context,
                                                fw_rule['firewall_policy_id'])

    def create_firewall(self, context, firewall):
        #LOG.debug(_("create_firewall() called"))
        tenant_id = self._get_tenant_id_for_create(context,
                                                   firewall['firewall'])
        fw_count = self.get_firewalls_count(context)
        #if fw_count:
        #    raise FirewallCountExceeded(tenant_id=tenant_id)
        #firewall['firewall']['status'] = const.PENDING_CREATE
        firewall['firewall']['status'] = const.ACTIVE
        fw = super(FirewallPlugin, self).create_firewall(context, firewall)
        fw_with_rules = (
            self._make_firewall_dict_with_rules(context, fw['id']))
        #self.agent_rpc.create_firewall(context, fw_with_rules)
        self.driver.firewall_config_update(context,fw['id'],fw_with_rules)
        return fw

    def update_firewall(self, context, id, firewall):
        #LOG.debug(_("update_firewall() called"))
        #self._ensure_update_firewall(context, id)
        #firewall['firewall']['status'] = const.PENDING_UPDATE
        firewall['firewall']['status'] = const.ACTIVE
        fw = super(FirewallPlugin, self).update_firewall(context, id, firewall)
        fw_with_rules = (
            self._make_firewall_dict_with_rules(context, fw['id']))
        #self.agent_rpc.update_firewall(context, fw_with_rules)
        self.driver.firewall_config_update(context,fw['id'],fw_with_rules)
        return fw

    def delete_db_firewall_object(self, context, id):
        firewall = self.get_firewall(context, id)
        if firewall['status'] in [const.PENDING_DELETE]:
            super(FirewallPlugin, self).delete_firewall(context, id)

    def delete_firewall(self, context, id):
        #LOG.debug(_("delete_firewall() called"))
        status_update = {"firewall": {"status": const.PENDING_DELETE}}
        fw = super(FirewallPlugin, self).update_firewall(context, id,
                                                         status_update)
        fw_with_rules = (
            self._make_firewall_dict_with_rules(context, fw['id']))
        self.driver.firewall_config_delete(context,fw['config_handle_id'],fw_with_rules)
        super(FirewallPlugin, self).delete_firewall(context, id)
        #self.agent_rpc.delete_firewall(context, fw_with_rules)
        
    def get_firewall(self, context, id, fields=None):
	#LOG.debug(_("get_firewall() called"))
	fw_details = super(FirewallPlugin, self).get_firewall(context, id)
        config_handle_id = fw_details['config_handle_id']
	if config_handle_id:
	    config_details = self.get_config_handle(context, config_handle_id)
	    fw_details.update({'config_mode': config_details['config_mode']})
	else:
	    fw_details.update({'config_mode': None})
        return fw_details


    def create_firewall_policy(self,context,firewall_policy):
        #LOG.debug(_("create_firewall_policy() called"))
        fwp = super(FirewallPlugin, self).create_firewall_policy(context, firewall_policy)
        return fwp
    
    def update_firewall_policy(self, context, id, firewall_policy):
        #LOG.debug(_("update_firewall_policy() called"))
        #self._ensure_update_firewall_policy(context, id)
        fwp = super(FirewallPlugin,
                    self).update_firewall_policy(context, id, firewall_policy)
        self._rpc_update_firewall_policy(context, id)
        return fwp

    def update_firewall_rule(self, context, id, firewall_rule):
        #LOG.debug(_("update_firewall_rule() called"))
        #self._ensure_update_or_delete_firewall_rule(context, id)
        fwr = super(FirewallPlugin,
                    self).update_firewall_rule(context, id, firewall_rule)
        firewall_policy_id = fwr['firewall_policy_id']
        if firewall_policy_id:
            self._rpc_update_firewall_policy(context, firewall_policy_id)
            pass
        return fwr

    def delete_firewall_rule(self, context, id):
        #LOG.debug(_("delete_firewall_rule() called"))
        #self._ensure_update_or_delete_firewall_rule(context, id)
        fwr = self.get_firewall_rule(context, id)
        firewall_policy_id = fwr['firewall_policy_id']
        super(FirewallPlugin, self).delete_firewall_rule(context, id)
        # At this point we have already deleted the rule in the DB,
        # however it's still not deleted on the backend firewall.
        # Until it gets deleted on the backend we will be setting
        # the firewall in PENDING_UPDATE state. The backend firewall
        # implementation is responsible for setting the appropriate
        # configuration (e.g. do not allow any traffic) until the rule
        # is deleted. Once the rule is deleted, the backend should put
        # the firewall back in ACTIVE state. While the firewall is in
        # PENDING_UPDATE state, the firewall behavior might differ based
        # on the backend implementation.
        if firewall_policy_id:
            self._rpc_update_firewall_policy(context, firewall_policy_id)
            pass

    def insert_rule(self, context, id, rule_info):
        #LOG.debug(_("insert_rule() called"))
        #self._ensure_update_firewall_policy(context, id)
        fwp = super(FirewallPlugin,
                    self).insert_rule(context, id, rule_info)
        self._rpc_update_firewall_policy(context, id)
        return fwp

    def remove_rule(self, context, id, rule_info):
        #LOG.debug(_("remove_rule() called"))
        #self._ensure_update_firewall_policy(context, id)
        fwp = super(FirewallPlugin,
                    self).remove_rule(context, id, rule_info)
        self._rpc_update_firewall_policy(context, id)
        return fwp
    
    def create_networkfunction(self, context, networkfunction):
        v = self.db.create_networkfunction(context, networkfunction)
        ###TODO::Network Service DRVIER TO HANDLE
        return v
    
    def update_networkfunction(self, context, networkfunction_id, networkfunction):
        #LOG.debug(_('Update networkfunction %s'), networkfunction_id)
        v_new = self.db.update_networkfunction(context, networkfunction_id, networkfunction)
        return v_new
    
    def delete_networkfunction(self, context, networkfunction_id):
        #LOG.debug(_('Delete networkfunction %s'), networkfunction_id)
        self.db.delete_networkfunction(context, networkfunction_id)
    
    def get_networkfunction(self, context, networkfunction_id, fields=None):
        #LOG.debug(_('Get networkfunction %s'), networkfunction_id)
        return self.db.get_networkfunction(context, networkfunction_id, fields)
    
    def get_networkfunctions(self, context, filters=None, fields=None):
        #LOG.debug(_('Get networkfunctions'))
        return self.db.get_networkfunctions(context, filters, fields)
    
    def create_config_handle(self, context, config_handle):
        v = self.db.create_config_handle(context, config_handle)
        ###TODO::Network Service DRVIER TO HANDLE
        return v
    
    def update_config_handle(self, context, config_handle_id, config_handle):
        #LOG.debug(_('Update config_handle %s'), config_handle_id)
        v_new = self.db.update_config_handle(context, config_handle_id, config_handle)
        return v_new
    
    def delete_config_handle(self, context, config_handle_id):
        #LOG.debug(_('Delete config_handle %s'), config_handle_id)
        self.db.delete_config_handle(context, config_handle_id)
    
    def get_config_handle(self, context, config_handle_id, fields=None):
        #LOG.debug(_('Get config_handle %s'), config_handle_id)
        return self.db.get_config_handle(context, config_handle_id, fields)
    
    def get_config_handles(self, context, filters=None, fields=None):
        #LOG.debug(_('Get config_handles'))
        return self.db.get_config_handles(context, filters, fields)
    
    def create_config(self, context, config):
        #res = super(FirewallPlugin,
        #            self).create_config(context, config)
        #with open('/tmp/srik.out', 'w+') as f:
        #    f.write(str(res))
        #    f.close()
        c = config['config']
        id = c['config_handle_id']
        slug = c['slug']
        version = c['version']
        filters = {}
        filters['config_handle_id']= [id]
        firewalls = super(FirewallPlugin,
                    self).get_firewalls(context, filters=filters)
        data = []
        for fw in firewalls:
            fw_with_rules = (
                self._make_firewall_dict_with_rules(context, fw['id']))
            data.append(fw_with_rules)
        res = {'config_handle_id': id,
            'response': data,
            'slug': slug,
            'version': version,
            'header': 'data'}
        return res
    
    def generate_firewall_config(self,context, config):
	LOG.debug(_('Generating Firewall Configuration %s'), str(config))
	ctx = crd_context.get_admin_context()
	data = self.create_config(ctx, config['body'])
	LOG.debug(_('Generated Firewall Configuration %s'), str(data))
	return {'config':data}
