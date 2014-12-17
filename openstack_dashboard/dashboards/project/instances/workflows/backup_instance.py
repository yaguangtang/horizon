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


class SetBackupChoiceAction(workflows.Action):
    backup = forms.ChoiceField(label=_("Backup type"),
                               required=True,
                               help_text=_("Instance backup type"))

    rotation = forms.ChoiceField(label=_("Rotation"),
                               required=True,
                               help_text=_("Rotation type"))
    class Meta:
        name = _("Backup choice")
        slug = 'backup_choice'
        help_text_template = ("project/instances/"
                              "_backup_help.html")

    def clean(self):
        cleaned_data = super(SetBackupChoiceAction, self).clean()
        flavor = cleaned_data.get('flavor', None)
        return cleaned_data

    def populate_backup_choices(self, request, context):
        backup_type = [('daily', 'daily'), ('weekly', 'weekly'),
                       ('monthly', 'monthly')]
        if backup_type:
            backup_type.insert(0, ("", _("Select backup type")))
        return backup_type

    def populate_rotation_choices(self, request, context):
        rotation = [(0,0), (1,1), (2,2), (3,3), (4,4), (5,5)]
        if rotation:
            rotation.insert(0, ("", _("Select rotation")))
        return rotation

    def get_help_text(self):
        extra = {}
        return super(SetBackupChoiceAction, self).get_help_text(extra)


class SetBackupChoice(workflows.Step):
    action_class = SetBackupChoiceAction
    depends_on = ("instance_id",)
    contributes = ( "backup", "rotation")


class BackupInstance(workflows.Workflow):
    slug = "backup_instance"
    name = _("Backup Instance")
    finalize_button_name = _("Backup")
    success_message = _('Scheduled backup of instance "%s".')
    failure_message = _('Unable to backup instance "%s".')
    success_url = "horizon:project:instances:index"
    default_steps = (SetBackupChoice,)

    def format_status_message(self, message):
        return message % self.context.get('name', 'unknown instance')

    @sensitive_variables('context')
    def handle(self, request, context):
        instance_id = context.get('instance_id', None)
        rotation = context.get('rotation', None)
        backup_type = context.get('backup', None)
        metadata = {'rotation': rotation, 'backup_type': backup_type}
        try:
            api.nova.server_meta(request, instance_id, metadata)
            return True
        except Exception:
            exceptions.handle(request)
            return False
