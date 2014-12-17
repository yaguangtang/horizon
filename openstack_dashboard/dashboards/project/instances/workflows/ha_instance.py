# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 CentRin Data, Inc.
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


import json

from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables  # noqa

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard import api

from openstack_dashboard.dashboards.project.instances \
    import utils as instance_utils


class SetHaChoiceAction(workflows.Action):
    ha = forms.ChoiceField(label=_("Instance HA"),
                               required=True,
                               help_text=_("Instance HA"))

    class Meta:
        name = _("HA choice")
        slug = 'ha_choice'
        help_text_template = ("project/instances/"
                              "_ha_help.html")


    def populate_ha_choices(self, request, context):
        instance_ha = [(True,True), (False,False)]
        if instance_ha:
            instance_ha.insert(0, ("", _("set instance HA")))
        return instance_ha

    def get_help_text(self):
        extra = {}
        return super(SetHaChoiceAction, self).get_help_text(extra)


class SetHaChoice(workflows.Step):
    action_class = SetHaChoiceAction
    depends_on = ("instance_id",)
    contributes = ("ha",)


class HaInstance(workflows.Workflow):
    slug = "ha_instance"
    name = _("Instance HA")
    finalize_button_name = _("Setup")
    success_message = _('Scheduled set instance to HA mode "%s".')
    failure_message = _('Unable to set instance HA "%s".')
    success_url = "horizon:project:instances:index"
    default_steps = (SetHaChoice,)

    def format_status_message(self, message):
        return message % self.context.get('name', 'unknown instance')

    @sensitive_variables('context')
    def handle(self, request, context):
        instance_id = context.get('instance_id', None)
        instance_ha = context.get('ha', False)
        metadata = {'instance_ha': instance_ha,}
        try:
            api.nova.server_meta(request, instance_id, metadata)
            return True
        except Exception:
            exceptions.handle(request)
            return False
