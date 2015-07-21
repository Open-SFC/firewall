# Copyright 2013 Freescale Semiconductor, Inc.
# All Rights Reserved
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
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging
from nscs.crdclient.v2_0 import client as crd_client

_logger = logging.getLogger(__name__)

class Client(object):
    """
    Firewall related Client Functions in CRD
    """
    networkfunctions_path = "/fw/networkfunctions"
    networkfunction_path = "/fw/networkfunctions/%s"
    config_handles_path = "/fw/config_handles"
    config_handle_path = "/fw/config_handles/%s"
    
    ##Firewall URLs
    firewall_rules_path = "/fw/firewall_rules"
    firewall_rule_path = "/fw/firewall_rules/%s"
    firewall_policies_path = "/fw/firewall_policies"
    firewall_policy_path = "/fw/firewall_policies/%s"
    firewall_policy_insert_path = "/fw/firewall_policies/%s/insert_rule"
    firewall_policy_remove_path = "/fw/firewall_policies/%s/remove_rule"
    firewalls_path = "/fw/firewalls"
    firewall_path = "/fw/firewalls/%s"
    fw_configs_path = "/fw/configs"
    
    FW_EXTED_PLURALS = {'firewall_rules': 'firewall_rule',
                     'firewall_policies': 'firewall_policy',
                     'firewalls': 'firewall',
                     }

    ################################################################
    ##                FWaaS Service Management                    ##
    ################################################################

    # Manage Firewall Rules	
    @crd_client.APIParamsCall
    def list_firewall_rules(self, retrieve_all=True, **_params):
        """Fetches a list of all firewall rules for a tenant."""
        # Pass filters in "params" argument to do_request

        return self.crdclient.list('firewall_rules', self.firewall_rules_path,
                         retrieve_all, **_params)

    @crd_client.APIParamsCall
    def show_firewall_rule(self, firewall_rule, **_params):
        """Fetches information of a certain firewall rule."""
        return self.crdclient.get(self.firewall_rule_path % (firewall_rule),
                        params=_params)

    @crd_client.APIParamsCall
    def create_firewall_rule(self, body=None):
        """Creates a new firewall rule."""
        return self.crdclient.post(self.firewall_rules_path, body=body)

    @crd_client.APIParamsCall
    def update_firewall_rule(self, firewall_rule, body=None):
        """Updates a firewall rule."""
        return self.crdclient.put(self.firewall_rule_path % (firewall_rule), body=body)

    @crd_client.APIParamsCall
    def delete_firewall_rule(self, firewall_rule):
        """Deletes the specified firewall rule."""
        return self.crdclient.delete(self.firewall_rule_path % (firewall_rule))

    # Manage Firewall Policies	

    @crd_client.APIParamsCall
    def list_firewall_policies(self, retrieve_all=True, **_params):
        """Fetches a list of all firewall policies for a tenant."""
        # Pass filters in "params" argument to do_request

        return self.crdclient.list('firewall_policies', self.firewall_policies_path,
                         retrieve_all, **_params)

    @crd_client.APIParamsCall
    def show_firewall_policy(self, firewall_policy, **_params):
        """Fetches information of a certain firewall policy."""
        return self.crdclient.get(self.firewall_policy_path % (firewall_policy),
                        params=_params)

    @crd_client.APIParamsCall
    def create_firewall_policy(self, body=None):
        """Creates a new firewall policy."""
        return self.crdclient.post(self.firewall_policies_path, body=body)

    @crd_client.APIParamsCall
    def update_firewall_policy(self, firewall_policy, body=None):
        """Updates a firewall policy."""
        return self.crdclient.put(self.firewall_policy_path % (firewall_policy),
                        body=body)

    @crd_client.APIParamsCall
    def delete_firewall_policy(self, firewall_policy):
        """Deletes the specified firewall policy."""
        return self.crdclient.delete(self.firewall_policy_path % (firewall_policy))

    @crd_client.APIParamsCall
    def firewall_policy_insert_rule(self, firewall_policy, body=None):
        """Inserts specified rule into firewall policy."""
        return self.crdclient.put(self.firewall_policy_insert_path % (firewall_policy),
                        body=body)

    @crd_client.APIParamsCall
    def firewall_policy_remove_rule(self, firewall_policy, body=None):
        """Removes specified rule from firewall policy."""
        return self.crdclient.put(self.firewall_policy_remove_path % (firewall_policy),
                        body=body)

    # Manage Firewalls

    @crd_client.APIParamsCall
    def list_firewalls(self, retrieve_all=True, **_params):
        """Fetches a list of all firewals for a tenant."""
        # Pass filters in "params" argument to do_request
        return self.crdclient.list('firewalls', self.firewalls_path, retrieve_all,
                         **_params)

    @crd_client.APIParamsCall
    def show_firewall(self, firewall, **_params):
        """Fetches information of a certain firewall."""
        return self.crdclient.get(self.firewall_path % (firewall), params=_params)

    @crd_client.APIParamsCall
    def create_firewall(self, body=None):
        """Creates a new firewall."""
        return self.crdclient.post(self.firewalls_path, body=body)

    @crd_client.APIParamsCall
    def update_firewall(self, firewall, body=None):
        """Updates a firewall."""
        return self.crdclient.put(self.firewall_path % (firewall), body=body)

    @crd_client.APIParamsCall
    def delete_firewall(self, firewall):
        """Deletes the specified firewall."""
        return self.crdclient.delete(self.firewall_path % (firewall))

    @crd_client.APIParamsCall
    def generate_firewall_config(self, body=None):
        """
        Generate the specified Firewall configuration
        """
        return self.crdclient.post(self.fw_configs_path, body=body)
    ##################### End of Firewall Management ####
    
    ####### Network Function API start######################################    
    @crd_client.APIParamsCall
    def list_networkfunctions(self, **_params):
        """
        Fetches a list of all networkfunctions for a tenant
        """
        # Pass filters in "params" argument to do_request
        return self.crdclient.get(self.networkfunctions_path, params=_params)
        
    @crd_client.APIParamsCall
    def create_networkfunction(self, body=None):
        """
        Creates a new Networkfunction
        """
        return self.crdclient.post(self.networkfunctions_path, body=body)
        
    @crd_client.APIParamsCall
    def delete_networkfunction(self, networkfunction):
        """
        Deletes the specified networkfunction
        """
        return self.crdclient.delete(self.networkfunction_path % (networkfunction))
    
    @crd_client.APIParamsCall
    def show_networkfunction(self, networkfunction, **_params):
        """
        Fetches information of a certain networkfunction
        """
        return self.crdclient.get(self.networkfunction_path % (networkfunction), params=_params)
        
    @crd_client.APIParamsCall
    def update_networkfunction(self, networkfunction, body=None):
        """
        Updates a networkfunction
        """
        return self.crdclient.put(self.networkfunction_path % (networkfunction), body=body)
    ####### Network Function API End######################################
    
    ####### Config handle API Begin######################################
    @crd_client.APIParamsCall
    def list_config_handles(self, **_params):
        """
        Fetches a list of all config_handles for a tenant
        """
        # Pass filters in "params" argument to do_request
        return self.crdclient.get(self.config_handles_path, params=_params)
        
    @crd_client.APIParamsCall
    def create_config_handle(self, body=None):
        """
        Creates a new Config_handle
        """
        return self.crdclient.post(self.config_handles_path, body=body)
        
    @crd_client.APIParamsCall
    def delete_config_handle(self, config_handle):
        """
        Deletes the specified config_handle
        """
        return self.crdclient.delete(self.config_handle_path % (config_handle))
    
    @crd_client.APIParamsCall
    def show_config_handle(self, config_handle, **_params):
        """
        Fetches information of a certain config_handle
        """
        return self.crdclient.get(self.config_handle_path % (config_handle), params=_params)
        
    @crd_client.APIParamsCall
    def update_config_handle(self, config_handle, body=None):
        """
        Updates a config_handle
        """
        return self.crdclient.put(self.config_handle_path % (config_handle), body=body)
    ####### Config handle API End######################################
        
    
    def __init__(self, **kwargs):
        self.crdclient = crd_client.Client(**kwargs)
        self.crdclient.EXTED_PLURALS.update(self.FW_EXTED_PLURALS)
        self.format = 'json'
    
