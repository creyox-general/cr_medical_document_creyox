# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.http import request
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    """Inherited AccountMove for new fields."""
    _inherit = 'account.move'

    movement_code = fields.Integer(string='Movement Code',
                                   compute="compute_movement_code")
    movement_code_string = fields.Char(string='Movement code',
                                       compute="compute_movement_code")
    is_for_hrp = fields.Boolean("Is HRP",
                                compute="compute_is_for_hrp")
    is_pos_entry = fields.Boolean("Is POS Entry")

    # Makes sure that there's only one VAT type in an entry
    @api.constrains('line_ids')
    def _check_restricted_accounts(self):
        restricted_accounts = {'111110', '111120'}

        for move in self:
            accounts_in_move = set(move.line_ids.mapped('account_id.code'))  # Get account codes in entry
            if restricted_accounts.issubset(accounts_in_move):  # Check if both are present
                raise ValidationError("Israeli and Palestinian VAT records cannot appear in the same journal entry.")  # Prevent user from saving the entry

    @api.depends("movement_code","movement_code_string")
    def compute_is_for_hrp(self):

        icpsudo = request.env['ir.config_parameter'].sudo()
        is_for_hrp = icpsudo.get_param(
            "bizzup_movein_report.is_for_hrp"
        )
        pos_session = self.env['pos.session'].search(
            [('move_id', '=', self.id)],limit=1)
        for rec in self:
            if pos_session:
                rec.with_context(bypass_write=True).write(
                    {'is_pos_entry': True})
                # self.is_pos_entry = True
            else:
                rec.with_context(bypass_write=True).write(
                    {'is_pos_entry': False})
                # self.is_pos_entry = False
            if is_for_hrp:
                rec.with_context(bypass_write=True).write(
                    {'is_for_hrp': True})
                # rec.is_for_hrp = True
            else:
                rec.with_context(bypass_write=True).write(
                    {'is_for_hrp': False})
                # rec.is_for_hrp = True

    @api.depends('move_type', 'journal_id', 'fiscal_position_id')
    def compute_movement_code(self):
        icpsudo = request.env['ir.config_parameter'].sudo()
        is_for_hrp = icpsudo.get_param(
            "bizzup_movein_report.is_for_hrp"
        )
        for rec in self:
            if is_for_hrp:
                rec.is_for_hrp = True
            movement_code = self.env['movement.code'].search([
                ('account_move_type', '=', rec.move_type),
            ], limit=1)
            rec.movement_code = movement_code.code
            rec.movement_code_string = movement_code.code_string
            if self.journal_id:
                journal_movement_code = self.env['movement.code'].search([
                    ('account_move_type', '=', rec.move_type),
                    ('journal_id', '=', rec.journal_id.id),
                    ('fiscal_id', '=', None),
                    ('means_of_payment', '=', '0')
                ], limit=1)
                if journal_movement_code:
                    rec.movement_code = journal_movement_code.code
                    rec.movement_code_string = journal_movement_code.code_string
                if not journal_movement_code:
                    rec.movement_code = movement_code.code
                    rec.movement_code_string = movement_code.code_string
                if rec.fiscal_position_id:
                    fiscal_movement_code = rec.env['movement.code'].search([
                        ('account_move_type', '=', rec.move_type),
                        ('journal_id', '=', rec.journal_id.id),
                        ('fiscal_id', '=', rec.fiscal_position_id.id)
                    ], limit=1)
                    if fiscal_movement_code:
                        rec.movement_code = fiscal_movement_code.code
                        rec.movement_code_string = fiscal_movement_code.code_string
                if rec.move_type == 'entry':
                    mop_movement_code = rec.env['movement.code'].search([
                        ('account_move_type', '=', rec.move_type),
                        ('journal_id', '=', rec.journal_id.id),
                        ('means_of_payment', '=',
                         rec.origin_payment_id.means_of_payment)
                    ], limit=1)
                    if mop_movement_code:
                        rec.movement_code = mop_movement_code.code
                        rec.movement_code_string = mop_movement_code.code_string
