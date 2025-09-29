#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class AccountPaymentLine(models.Model):
    _name = "lyg.account.payment.line"
    _description = "Payment Lines"

    @api.model
    def default_get(self, fields):
        """Pass default value for amount field using context."""
        res = super(AccountPaymentLine, self).default_get(fields)
        context = self.env.context.copy()
        res.update({
            'amount': context.get('amount')
        })
        return res

    pay_invoice_id = fields.Many2one("account.move", "Move")
    journal_id = fields.Many2one('account.journal', "Journal")
    currency_id = fields.Many2one(related='pay_invoice_id.currency_id')
    credit_account_no = fields.Char(string="Credit/Account Number")
    branch = fields.Char(string="Branch")
    bank_id = fields.Many2one('res.bank', string="Bank")
    voucher_check_no = fields.Char(string="Voucher/Check Number")
    validity_date = fields.Date(string="Redemption/Validity Date")
    amount = fields.Monetary(
        "Amount", currency_field='currency_id')
    means_of_payment = fields.Selection(
        [('1', 'Cash'), ('2', 'Check'), ('3', 'Credit Card'),
         ('4', 'Bank Transfer'), ('5', 'Gift Card'), ('6', 'Return Note'),
         ('7', 'Promissory Note'), ('8', 'Standing Order'), ('9', 'Other')],
        default='1')
    bank_id = fields.Many2one('res.bank', "Bank")

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        """Before adding payment lines, please add invoiceable lines"""
        invoice_lines = self.pay_invoice_id.invoice_line_ids
        if not invoice_lines:
            raise ValidationError(
                _("Before adding payment lines, please add invoiceable lines"))
