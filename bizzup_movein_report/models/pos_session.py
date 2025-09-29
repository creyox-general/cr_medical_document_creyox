# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PosSession(models.Model):
    """Inherited PosSession for new functionality."""
    _inherit = 'pos.session'

    def _create_account_move(self, balancing_account=False,
                             amount_to_balance=0,
                             bank_payment_method_diffs=None):
        res = super()._create_account_move(balancing_account,
                                           amount_to_balance,
                                           bank_payment_method_diffs)
        if self.move_id:
            self.move_id.is_pos_entry = True
        return res
