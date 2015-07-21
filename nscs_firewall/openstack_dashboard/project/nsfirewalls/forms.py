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

import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from openstack_dashboard import api
from horizon import exceptions
from horizon import forms
from horizon import messages


LOG = logging.getLogger(__name__)

class BaseConfigForm(forms.SelfHandlingForm):
    def __init__(self, request, *args, **kwargs):
        super(BaseConfigForm, self).__init__(request, *args, **kwargs)
        # Populate Firewall choices
        fw_choices = [('', _("Select a Firewall"))]
        firewalls = api.crdfwaas.firewalls_list(request)
        for fw in firewalls:
            fw_choices.append((fw.id, fw.name))
        self.fields['fw_id'].choices = fw_choices

class MapFirewall(BaseConfigForm):
    config_handle_id = forms.CharField(label=_("Config ID"),
                                 widget=forms.TextInput(
                                     attrs={'readonly': 'readonly'}))
    fw_id = forms.ChoiceField(label=_("Firewalls"),
                                        required=True,
                                        help_text=_("Select one of the"
                                                    "Firewalls available"))
    tenant_id = forms.CharField(widget=forms.HiddenInput)
        
    failure_url = 'horizon:project:nsfirewalls:index'

    def handle(self, request, data):
        try:
            LOG.debug('params = %s' % data)
            config = api.crdfwaas.firewall_update(request, data['fw_id'],
                                               config_handle_id=data['config_handle_id'])
            msg = _('Firewall was successfully mapped for the Configuration %s.') % data['config_handle_id']
            LOG.debug(msg)
            messages.success(request, msg)
            return config
        except Exception:
            msg = _('Failed to map Firewall for the COnfiguration %s') % data['config_handle_id']
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
            
class UpdateConfig(forms.SelfHandlingForm):
    config_id = forms.CharField(label=_("ID"),
                                 widget=forms.TextInput(
                                     attrs={'readonly': 'readonly'}))
    name = forms.CharField(label=_("Configuration Name"),
                                  required=True,
                                  initial="",
                                  help_text=_("Name of the Configuration"))
    tenant_id = forms.CharField(widget=forms.HiddenInput)
        
    failure_url = 'horizon:project:nsfirewalls:index'

    def handle(self, request, data):
        try:
            LOG.debug('params = %s' % data)
            #params = {'name': data['name']}
            #params['gateway_ip'] = data['gateway_ip']
            config = api.crdfwaas.config_handle_modify(request, data['config_id'],
                                               name=data['name'])
            msg = _('Configuration %s was successfully updated.') % data['config_id']
            LOG.debug(msg)
            messages.success(request, msg)
            return config
        except Exception:
            msg = _('Failed to update Configuration %s') % data['name']
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
            
class UnMapFirewall(forms.SelfHandlingForm):
    config_handle_id = forms.CharField(label=_("Config ID"),
                                 widget=forms.TextInput(
                                     attrs={'readonly': 'readonly'}))
    fw_id = forms.CharField(label=_("Firewall ID"),
                                 widget=forms.TextInput(
                                     attrs={'readonly': 'readonly'}))
    failure_url = 'horizon:project:nsfirewalls:index'

    def handle(self, request, data):
        try:
            LOG.debug('params = %s' % data)
            config = api.crdfwaas.firewall_update(request, data['fw_id'],
                                               config_handle_id='')
            msg = _('Firewall was successfully dettached for the Configuration %s.') % data['config_handle_id']
            LOG.debug(msg)
            messages.success(request, msg)
            return config
        except Exception:
            msg = _('Failed to dettach Firewall for the Configuration %s') % data['config_handle_id']
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
