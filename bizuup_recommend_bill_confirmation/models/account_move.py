# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, api, fields, _
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang

class AccountMove(models.Model):
    _inherit = 'account.move'

    check_9_digits = fields.Boolean(
        string="Check 9 Digits",
        compute="_compute_check_9_digits",
        store=True,
    )

    @api.depends('rt_confirmation_number', 'move_type')
    def _compute_check_9_digits(self):
        for move in self:
            if move.move_type in ('in_invoice', 'in_refund') and move.rt_confirmation_number:
                move.check_9_digits = len(move.rt_confirmation_number) >= 10
            else:
                move.check_9_digits = False
