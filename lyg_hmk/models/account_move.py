#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################
# from odoo.addons.account.models.account_move import AccountMove as ActionPost
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.http import request


_logger = logging.getLogger(__name__)
tax_value = 0.0


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _search_default_journal(self):
        res = super(AccountMove, self)._search_default_journal()
        if self.is_hmk:
            journal = self.env['account.journal'].search(
                [('code', '=', 'HMK')])
            return journal.id
        return res

    @api.depends('payment_lines.amount', 'withholding_amount')
    def _total_payment_amount(self):
        """Function calculate payment lines total amount"""
        for rec in self:
            if rec.is_hmk and rec.payment_lines:
                rec.total_pay_amount = sum(rec.payment_lines.mapped('amount'))
                rec.total_pay_amount = sum(rec.payment_lines.mapped('amount')) + self.withholding_amount
            else:
                rec.total_pay_amount = 0.0

    payment_lines = fields.One2many('lyg.account.payment.line', 'pay_invoice_id')
    is_hmk = fields.Boolean(related="journal_id.is_hmk")
    total_pay_amount = fields.Monetary(
        "Paid + Withholding amount", compute="_total_payment_amount",
        store=True, currency_field='currency_id')
    withholding_amount = fields.Monetary("Withholding Tax Amount", currency_field='currency_id', copy=False)
    withholding_tax_process = fields.Boolean(related="company_id.withholding_tax_process")
    remain_amount_hmk = fields.Float(compute="_compute_remain_amount_hmk", store=True)

    @api.depends_context("payment_lines", "payment_lines.amount", "amount_total")
    @api.depends("payment_lines", "payment_lines.amount", "amount_total", "withholding_amount")
    def _compute_remain_amount_hmk(self):
        """Function call to compute default amount for lines."""
        for rec in self:
            if rec.journal_id.is_hmk:
                rec.remain_amount_hmk = rec.amount_total - sum(
                    rec.payment_lines.mapped("amount")) - rec.withholding_amount

    def create_hmk_payment(self):
        """create payment lines"""
        to_reconcile = []
        for line in self.payment_lines:
            batches = self._get_payment_lines()
            reconcile_list = []
            # append lines in it
            to_reconcile.append(batches[0]['lines'])
            payment_vals = {
                'date': self.date,
                'amount': line.amount,
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'memo': line.pay_invoice_id.name,
                'currency_id': self.currency_id.id,
                'journal_id': line.journal_id.id,
                'partner_id': self.partner_id.id,
                'is_hmk_payment': self.is_hmk,
                'invoice_ids': [(6, 0, self.ids)]
            }
            # Payment Created
            if self.company_id.withholding_tax_process and self.withholding_amount:
                if self.withholding_amount >= self.total_pay_amount:
                    raise ValidationError(_("Write off amount is not grater or same than Total Payable Amount..!!"))
                last_payment_line = self.payment_lines[-1]
                if line.id == last_payment_line.id:
                    payment_vals['withholding_line_vals'] = {
                        'name': 'HMK-Withholding Payment',
                        'amount': self.withholding_amount,
                        'account_id': self.company_id.cust_withholding_tax_account_id.id,
                    }
                    payment_vals.update({
                        'hmk_withholding_payment': True,
                    })
            payment_value_list = [payment_vals]
            payments = self.env['account.payment'].create(payment_value_list)
            payments.action_post()
            domain = [('account_type', 'in', ('asset_receivable', 'liability_payable')), ('reconciled', '=', False)]
            for payment, lines in zip(payments, to_reconcile):
                payment_lines = payment.move_id.line_ids.filtered_domain(
                    domain)
                # Reconcile Payment and Invoice
                for account in payment_lines.account_id:
                    (payment_lines + lines) \
                        .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)]) \
                        .reconcile()
                if payment.name == "/" and self.company_id.withholding_tax_process and self.withholding_amount:
                    payment.name = payment.move_id.name
            payments.action_validate()

    def action_post(self):
        """Function Inherit to pass invoice data to tranzila."""
        res = super(AccountMove, self).action_post()
        icpsudo = request.env['ir.config_parameter'].sudo()
        vat_limit = icpsudo.get_param(
            "l10n_il_lyg.vat_limit"
        )
        for rec in self:
            if rec.is_hmk and rec.move_type == 'out_invoice' and 'hmk_tranzila' not in rec._context and 'hmk_i4u' not in rec._context and 'hmk_greeninvoice' not in rec._context:
                if rec.partner_id and rec.partner_id.company_type == 'company' and not rec.partner_id.vat:
                    raise ValidationError(
                        _("Please insert VAT ID on the selected Customer/Vendor."))
                if rec.partner_id and not rec.partner_id.vat and rec.amount_total > int(vat_limit):
                    raise ValidationError(
                        _(
                            "Please insert VAT ID on the selected Customer/Vendor."
                            )
                    )
            # Checked Only HMK Flag set
            if rec.is_hmk and round(rec.amount_residual, 2) != round(rec.total_pay_amount, 2):
                raise ValidationError(_("To confirm HMK invoice, payment amount must be same as Total!!"))
            else:
                rec.create_hmk_payment()
        return res

    @api.model
    def _get_line_multi_key(self, line):
        """Function Generate key for payment"""
        return {
            'partner_id': line.partner_id.id,
            'account_id': line.account_id.id,
            'currency_id': (line.currency_id or line.company_currency_id).id,
            'partner_bank_id': (line.move_id.partner_bank_id or line.partner_id.commercial_partner_id.bank_ids[:1]).id,
            'partner_type': 'customer' if line.account_type == 'asset_receivable' else 'supplier',
            'payment_type': 'inbound' if line.balance > 0.0 else 'outbound',
        }

    def _get_payment_lines(self):
        """Function get payment line."""
        self.ensure_one()
        lines = self.line_ids.filtered(lambda l: l.account_type in ('asset_receivable', 'asset_payable'))._origin
        batches = {}
        for line in lines:
            batch_key = self._get_line_multi_key(line)
            serialized_key = '-'.join(str(v) for v in batch_key.values())
            batches.setdefault(serialized_key, {
                'key_values': batch_key,
                'lines': self.env['account.move.line'],
            })
            batches[serialized_key]['lines'] += line
        return list(batches.values())


