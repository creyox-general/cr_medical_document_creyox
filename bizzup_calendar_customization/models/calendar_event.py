# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields
from datetime import datetime


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    priority_code = fields.Selection(
        selection=[('1', 'Yes'), ('2', 'No'), ('3', 'Rejected 1'), ('4', 'Rejected 2')],
        string='Priority Code'
    )
    # activity_id = fields.Many2one(comodel_name='mail.activity',
    #                               string='Activity')

    def action_find_replacement_meeting(self):
        """
        #HT01661
        Display the future meetings with some filters applied.
        :return: Tree view of meetings
        """
        self.ensure_one()
        domain = [('partner_ids', '!=', False)]
        # domain = [('partner_ids', '!=', False),
        #           ('start', '>', datetime.now()), '|',
        #           ('activity_id', '=', self.activity_id.id),
        #           ('priority_code', 'in', ['2', '3'])]
        # TODO:- remove below code after confirmation
        # action = self.env["ir.actions.actions"]._for_xml_id(
        #     "calendar.action_calendar_event")
        context = {
            'search_default_search_priority_1_3': 1,
            'search_default_search_future_only': 1,
            'start_date': self.start or False,
            # 'activity_id': self.activity_id.id,
        }
        return {
            'type': 'ir.actions.act_window',
            'name': 'Find Replacement Meeting',
            'res_model': 'calendar.event',
            'view_mode': 'list,form',
            'search_view_id': (self.env.ref(
                'calendar.view_calendar_event_search').id, 'search'),
            'target': 'current',
            'context': context,
            # 'domain': [('partner_ids', 'in', self.env.user.partner_id.ids)],
            'domain': domain,
        }
