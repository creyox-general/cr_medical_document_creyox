# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.http import request


class MovementCode(models.Model):
    """New Custom Model for Movement Code."""
    _name = 'movement.code'
    _description = 'Movement Code'

    def get_subtype_selection(self):
        selection = []
        domain = []
        if self.account_move_type == 'entry':
            domain += [('type', 'in', ('bank', 'cash', 'general'))]
        journal_entry = self.env['account.journal'].search(domain)
        for rec in journal_entry:
            selection += [('%s' % rec.name, '%s' % rec.name)]
        return selection


    name = fields.Char("Name")
    code = fields.Integer("Code", copy=False)
    code_string = fields.Char(" ", copy=False)
    is_hrp = fields.Boolean("Is HRP", compute="_compute_is_hrp")
    Details = fields.Text("Details")
    account_move_type = fields.Selection(
        selection=[
            ('entry', 'Journal Entry'),
            ('out_invoice', 'Customer Invoice'),
            ('out_refund', 'Customer Credit Note'),
            ('in_invoice', 'Vendor Bill'),
            ('in_refund', 'Vendor Credit Note'),
            ('out_receipt', 'Sales Receipt'),
            ('in_receipt', 'Purchase Receipt'),
        ],
        string='Type',
        required=True,
        index=True,
    )
    journal_id = fields.Many2one('account.journal', string='Sub Type')
    fiscal_id = fields.Many2one('account.fiscal.position',
                                string='Fiscal Position')
    means_of_payment = fields.Selection(
        [('0', ''), ('1', 'Cash'), ('2', 'Check'), ('3', 'Credit Card'),
         ('4', 'Bank Transfer'), ('5', 'Gift Card'), ('6', 'Return Note'),
         ('7', 'Promissory Note'), ('8', 'Standing Order'), ('9', 'Other')],
        default='0')

    _sql_constraints = [('code_uniq', 'unique (code)',
                         'The Code must be unique')]

    _sql_constraints = [('code_string_uniq', 'unique (code_string)',
                         'The Code must be unique')]

    @api.depends("name")
    def _compute_is_hrp(self):
        icpsudo = request.env['ir.config_parameter'].sudo()
        is_for_hrp = icpsudo.get_param(
            "bizzup_movein_report.is_for_hrp"
        )
        for rec in self:
            if is_for_hrp:
                rec.is_hrp = True
            else:
                rec.is_hrp = False

    @api.model_create_multi
    def create(self, vals_list):
        """Inherited Create function for external_software_code > 8
        Validation"""
        code = str(vals_list[0].get('code'))
        if self.is_hrp:
            self.movement_code = 0
        if len(code) > 3:
            raise ValidationError(
                _("You cannot enter more than 3 digits in Code."))
        existing_movement_code = self.env['movement.code'].search([(
            'account_move_type', '=', vals_list[0].get('account_move_type')),
            ('journal_id', '=', vals_list[0].get('journal_id'))])
        if vals_list[0].get('code'):
            vals_list[0]['code_string'] = str(vals_list[0].get('code'))
        if vals_list[0].get('code_string'):
            code_string = vals_list[0].get('code_string').isdigit()
            vals_list[0]['code'] = int(
                vals_list[0].get('code_string')) if code_string else 0
        for rec in existing_movement_code:
            if existing_movement_code and (rec.account_move_type != 'entry' and not vals_list[0].get('fiscal_id')):
                raise ValidationError(
                    _("The Combination already Exist in Other Record.")
                )
            if existing_movement_code and (rec.account_move_type == 'entry' and vals_list[0].get('means_of_payment') == '0'):
                raise ValidationError(
                    _("The Combination already Exist in Other Record.")
                )
            if vals_list[0].get('means_of_payment') != '0':
                means_of_payment_code = existing_movement_code.search([
                    ('account_move_type', '=', 'entry'),
                    ('means_of_payment', '=', vals_list[0].get('means_of_payment'))
                ], limit=1)
                if means_of_payment_code:
                    raise ValidationError(
                        _("The Combination already Exist in Other Record.")
                    )
            if vals_list[0].get('fiscal_id'):
                fiscal_movement_code = existing_movement_code.search([(
                    'account_move_type', '=',
                    vals_list[0].get('account_move_type')),
                    ('journal_id', '=', vals_list[0].get('journal_id')),
                    ('fiscal_id', '=', vals_list[0].get('fiscal_id')
                     )], limit=1)
                if fiscal_movement_code:
                    raise ValidationError(
                        _("The Combination already Exist in Other Record.")
                    )
        return super(MovementCode, self).create(vals_list)

    def write(self, vals):
        """Inherited Write function for external_software_code > 8
                Validation"""
        existing_movement_code = self.env['movement.code'].search([(
            'account_move_type', '=', vals.get('account_move_type') or self.account_move_type),
            ('journal_id', '=', vals.get('journal_id')) or self.journal_id.id], limit=1)
        if existing_movement_code:
            if existing_movement_code and not vals.get('fiscal_id') and not vals.get('means_of_payment'):
                raise ValidationError(
                    _("The Combination already Exist in Other Record.")
                )
        if vals.get('fiscal_id') or self.fiscal_id:
            existing_movement_code_fiscal_id = self.env['movement.code'].search([(
                'account_move_type', '=', vals.get('account_move_type') or self.account_move_type),
                ('journal_id', '=', vals.get('journal_id') or self.journal_id.id),
                ('fiscal_id', '=', vals.get('fiscal_id') or self.fiscal_id.id)
            ], limit=1)
            if existing_movement_code_fiscal_id:
                raise ValidationError(
                    _("The Combination already Exist in Other Record.")
                )
        if vals.get('means_of_payment') != '0' or self.means_of_payment != '0':
            existing_movement_means_of_payment = self.env['movement.code'].search([(
                'account_move_type', '=', vals.get('account_move_type') or self.account_move_type),
                ('journal_id', '=', vals.get('journal_id') or self.journal_id.id),
                ('means_of_payment', '!=', '0'),
                ('means_of_payment', '=', vals.get('means_of_payment') or self.means_of_payment)
            ])
            if existing_movement_means_of_payment:
                raise ValidationError(
                    _("The Combination already Exist in Other Record.")
                )
        return super(MovementCode, self).write(vals)
