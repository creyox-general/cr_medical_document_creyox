# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    """Inherited AccountJournal for new fields."""
    _inherit = 'account.journal'

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        context = self._context
        if context.get('movement_id'):
            movement_id = self.env['movement.code'].browse(context.get('movement_id'))
            if movement_id:
                if movement_id.account_move_type == 'entry':
                    domain += [('type', 'in', ('bank', 'cash'))]
                elif movement_id.account_move_type == 'out_invoice':
                    domain += [('type', '=', 'sale')]
                elif movement_id.account_move_type == 'out_refund':
                    domain += [('type', '=', 'sale')]
                elif movement_id.account_move_type == 'in_invoice':
                    domain += [('type', '=', 'purchase')]
                elif movement_id.account_move_type == 'in_refund':
                    domain += [('type', '=', 'purchase')]
                else:
                    domain += [('type', '=', 'gereral')]
        return super()._search(domain, offset, limit, order)
