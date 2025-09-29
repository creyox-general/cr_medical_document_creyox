# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_l10n_installed = fields.Boolean(related="company_id.is_l10n_installed")

    @api.onchange('type')
    def _onchange_mode_type_hash_table(self):
        """Added onchange to make hash table true for Bank and Cash type Journal"""
        if self.is_l10n_installed:
            if self.type and self.type not in ['bank', 'cash']:
                self.restrict_mode_hash_table = True
