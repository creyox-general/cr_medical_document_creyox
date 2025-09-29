# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields


class ResPartner(models.Model):
    """
    Inherits res.partner to link related partner call history records.
    Adds a one2many field to display call history on the contact form.
    """
    _inherit = 'res.partner'

    partner_call_history_ids = fields.Many2many(
        'partner.call.history',
        string='Call History'
    )
