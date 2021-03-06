# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Cisco Systems, Inc.
# Copyright 2012 NEC Corporation
# Copyright 2013 Freescale Semiconductor, Inc.
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

from __future__ import absolute_import

import logging

from nscs_firewall.crdclient.v2_0 import client as fw_client
from django.utils.datastructures import SortedDict

from horizon.conf import HORIZON_CONFIG

from openstack_dashboard.api import base
from openstack_dashboard.api import network
from openstack_dashboard.api import nova


LOG = logging.getLogger(__name__)



class CrdAPIDictWrapper(base.APIDictWrapper):

    def set_id_as_name_if_empty(self, length=8):
        try:
            if not self._apidict['name']:
                id = self._apidict['id']
                if length:
                    id = id[:length]
                self._apidict['name'] = '(%s)' % id
        except KeyError:
            pass

    def items(self):
        return self._apidict.items()
        
def crdclient(request):
    LOG.debug('crdfwclient connection created using token "%s" and url "%s"'
              % (request.user.token.id, base.url_for(request, 'crd')))
    LOG.debug('user_id=%(user)s, tenant_id=%(tenant)s' %
              {'user': request.user.id, 'tenant': request.user.tenant_id})
    c = fw_client.Client(token=request.user.token.id,
                              endpoint_url=base.url_for(request, 'crd'))
    return c

class Config_handle(CrdAPIDictWrapper):
    """Wrapper for crd config_handles"""
    _attrs = ['name', 'id', 'description', 'tenant_id', 'shared', 'config_mode']

    def __init__(self, apiresource):
        super(Config_handle, self).__init__(apiresource)

def config_handle_list(request, **params):
    LOG.debug("config_handle_list(): params=%s" % (params))
    config_handles = crdclient(request).list_config_handles(**params).get('config_handles')
    return [Config_handle(n) for n in config_handles]

def config_handle_list_for_tenant(request, tenant_id, **params):
    LOG.debug("config_handle_list_for_tenant(): tenant_id=%s, params=%s"
              % (tenant_id, params))
    config_handles = config_handle_list(request, tenant_id=tenant_id,
                            shared=False, **params)

    #config_handles += config_handle_list(request, shared=True, **params)

    return config_handles

def config_handle_create(request, **kwargs):
    LOG.debug("config_handle_create(): kwargs = %s" % kwargs)
    body = {'config_handle': kwargs}
    config_handle = crdclient(request).create_config_handle(body=body).get('config_handle')
    return Config_handle(config_handle)

def config_handle_delete(request, config_handle_id):
    LOG.debug("config_handle_delete(): catid=%s" % config_handle_id)
    crdclient(request).delete_config_handle(config_handle_id)
    
def config_handle_modify(request, config_handle_id, **kwargs):
    LOG.debug("config_handle_modify(): cateid=%s, params=%s" % (config_handle_id, kwargs))
    body = {'config_handle': kwargs}
    config_handle = crdclient(request).update_config_handle(config_handle_id,
                                                    body=body).get('config_handle')
    return Config_handle(config_handle)    

def config_handle_get(request, config_handle_id, **params):
    LOG.debug("config_handle_get(): catid=%s, params=%s" % (config_handle_id, params))
    config_handle = crdclient(request).show_config_handle(config_handle_id,
                                                  **params).get('config_handle')
    return Config_handle(config_handle)

class Networkfunction(CrdAPIDictWrapper):
    """Wrapper for crd networkfunctions"""
    _attrs = ['name', 'id', 'description', 'tenant_id', 'shared']

    def __init__(self, apiresource):
        super(Networkfunction, self).__init__(apiresource)

def networkfunction_list(request, **params):
    LOG.debug("networkfunction_list(): params=%s" % (params))
    networkfunctions = crdclient(request).list_networkfunctions(**params).get('networkfunctions')
    return [Networkfunction(n) for n in networkfunctions]

def networkfunction_list_for_tenant(request, tenant_id, **params):
    LOG.debug("networkfunction_list_for_tenant(): tenant_id=%s, params=%s"
              % (tenant_id, params))

    networkfunctions = networkfunction_list(request, tenant_id=tenant_id,
                            shared=False, **params)

    networkfunctions += networkfunction_list(request, shared=True, **params)

    return networkfunctions

def networkfunction_create(request, **kwargs):
    LOG.debug("networkfunction_create(): kwargs = %s" % kwargs)
    body = {'networkfunction': kwargs}
    networkfunction = crdclient(request).create_networkfunction(body=body).get('networkfunction')
    return Networkfunction(networkfunction)

def networkfunction_delete(request, networkfunction_id):
    LOG.debug("networkfunction_delete(): catid=%s" % networkfunction_id)
    crdclient(request).delete_networkfunction(networkfunction_id)
    
def networkfunction_modify(request, networkfunction_id, **kwargs):
    LOG.debug("networkfunction_modify(): cateid=%s, params=%s" % (networkfunction_id, kwargs))
    body = {'networkfunction': kwargs}
    networkfunction = crdclient(request).update_networkfunction(networkfunction_id,
                                                    body=body).get('networkfunction')
    return Networkfunction(networkfunction)    

def networkfunction_get(request, networkfunction_id, **params):
    LOG.debug("networkfunction_get(): catid=%s, params=%s" % (networkfunction_id, params))
    networkfunction = crdclient(request).show_networkfunction(networkfunction_id,
                                                  **params).get('networkfunction')
    return Networkfunction(networkfunction)   

###CRD Firewalls
class Firewall(CrdAPIDictWrapper):
    """Wrapper for neutron firewall"""

    def get_dict(self):
        firewall_dict = self._apidict
        firewall_dict['firewall_id'] = firewall_dict['id']
        return firewall_dict
    
def firewalls_list(request, **kwargs):
    return _firewalls_list(request, **kwargs)


def _firewalls_list(request, **kwargs):
    firewalls = crdclient(request).list_firewalls(
        **kwargs).get('firewalls')
    return [Firewall(f) for f in firewalls]


def firewall_get(request, firewall_id):
    return _firewall_get(request, firewall_id)


def _firewall_get(request, firewall_id):
    firewall = crdclient(request).show_firewall(
        firewall_id).get('firewall')
    return Firewall(firewall)
    
def firewall_update(request, firewall_id, **kwargs):
    body = {'firewall': kwargs}
    firewall = crdclient(request).update_firewall(
        firewall_id, body).get('firewall')
    return Firewall(firewall)