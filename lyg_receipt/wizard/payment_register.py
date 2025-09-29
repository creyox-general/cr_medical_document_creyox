#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################

from odoo import models, fields, api, _
import datetime

import logging
_logger = logging.getLogger(__name__)


class AccountPaymentRegister(models.TransientModel):
    _name = 'account.payment.wizard'
    _description = 'Payment Register'

    currency_id = fields.Many2one('res.currency')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)
    company_currency_id = fields.Many2one('res.currency',
                                          string="Company Currency",
                                          related='company_id.currency_id')
    line_ids = fields.Many2many('account.move.line',
                                'account_payment_wizard_move_line_rel',
                                'wizard_id', 'move_line_id'
                                , string="Journal items", readonly=True,
                                copy=False)
    invoice_receipt_line_ids = fields.One2many('payment.receipt.line',
                                               'pay_inv_id',
                                               "Invoice Payment Lines")
    remain_amount = fields.Char()

    @api.model
    def default_get(self, fields_list):
        """Function work to get default lines of selected invoice id."""
        res = super().default_get(fields_list)
        if 'active_id' in self._context:
            active_id = self.env['lyg.account.receipt'].browse(
                self._context.get('active_id'))
            available_lines = self.env['account.move.line']
            payment_lines = []
            _logger.info("\n\n active_id.receipt_line_ids", active_id.receipt_line_ids, active_id.remain_amount)
            # Get remaning payment amount lines to give option of keep open or write off to user.
            for pay_line in active_id.receipt_line_ids.filtered(
                    lambda inv: inv.type == 'invoice' and inv.invoice_id.amount_residual != eval(
                        active_id.remain_amount).get(inv.invoice_id.id,
                                                     0)).mapped('invoice_id'):
                vals = {'invoice_id': pay_line.id}
                payment_lines.append((0, 0, vals))
            # Get invoices receivable and payable lines(account.move)
            for pay_line in active_id.receipt_line_ids.filtered(
                    lambda inv: inv.type == 'invoice'):
                invoice_id = pay_line.invoice_id
                lines = self.env['account.move'].search(
                    [('id', '=', invoice_id.id)]).line_ids
                res['currency_id'] = active_id.currency_id.id
                for line in lines:
                    if line.account_type not in (
                            'asset_receivable', 'liability_payable'):
                        continue
                    if line.company_currency_id.is_zero(line.amount_residual):
                        continue
                    available_lines |= line
                res['line_ids'] = [(6, 0, available_lines.ids)]
            # Created remain invoice receipt lines
            res.update({'invoice_receipt_line_ids': payment_lines})
        return res

    @api.model
    def _get_line_multi_key(self, line):
        """Function Generate key for payment"""
        return {
            'partner_id': line.partner_id.id,
            'account_id': line.account_id.id,
            'currency_id': (line.currency_id or line.company_currency_id).id,
            'partner_bank_id': (
                        line.move_id.partner_bank_id or line.partner_id.commercial_partner_id.bank_ids[
                                                        :1]).id,
            'partner_type': 'customer' if line.account_type == 'asset_receivable' else 'supplier',
            'payment_type': 'inbound' if line.balance > 0.0 else 'outbound',
        }

    def _get_payment_lines(self):
        """Function get payment line."""
        self.ensure_one()
        lines = self.line_ids._origin
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

    def action_create_payment(self):
        """Function create payment with open and write-off option"""
        if 'active_id' in self._context:
            active_id = self.env['lyg.account.receipt'].browse(
                self._context.get('active_id'))
            dict_len = eval(active_id.remain_amount)
            to_reconcile = []
            batches = self._get_payment_lines()
            if len(dict_len) > 1:
                new_batches = []
                for batch_result in batches:
                    for line_move in batch_result['lines']:
                        new_batches.append({
                            **batch_result,
                            'lines': line_move,
                        })
                batches = new_batches
            for batch_result in batches:
                to_reconcile.append(batch_result['lines'])

            pay_dict = {}
            withholding_amount = 0
            for line in active_id.receipt_line_ids.filtered(
                    lambda l: l.type == 'invoice'):
                line.write({'state': 'post'})
                withholding_amount = line.withholding_amount
                amount = line.amount - line.withholding_amount if self.company_id.withholding_tax_process and line.withholding_amount else line.amount
                # append lines in it
                # payment values for open and write-off
                payment_vals = {
                    'date': datetime.datetime.now(),
                    'amount': amount,
                    'company_id':self.company_id.id,
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'memo': line.invoice_id.name,
                    'currency_id': self.currency_id.id,
                    'journal_id': line.journal_id.id,
                    'partner_id': active_id.partner_id.id,
                    'receipt_id': active_id.id,
                    'means_of_payment': line.means_of_payment or False
                }
                # append write off vals in payment value
                pay_line_write_off = self.invoice_receipt_line_ids.filtered(
                    lambda
                        l: l.payment_difference_handling == 'reconcile' and l.invoice_id == line.invoice_id)
                if pay_line_write_off:
                    last_payment_line = sorted(
                        active_id.receipt_line_ids.filtered(lambda
                                                                inv: inv.invoice_id == pay_line_write_off.invoice_id))
                    if last_payment_line and line.id == last_payment_line[
                        -1].id:
                        # Append write-off
                        payment_vals['write_off_line_vals'] = [{
                            'name': pay_line_write_off.write_off_label,
                            'amount_currency': pay_line_write_off.payment_diff,
                            'account_id': pay_line_write_off.write_off_account_id.id,
                            'balance': pay_line_write_off.payment_diff,

                        }]
                if self.company_id.withholding_tax_process:
                    if line.withholding_amount:
                        # Append Write Off
                        payment_vals['withholding_line_vals'] = {
                            'name': 'Withholding Payment',
                            'amount': line.withholding_amount,
                            'account_id': self.company_id.cust_withholding_tax_account_id.id,
                            'withholding_tax_process': True,

                        }
                        payment_vals.update({
                            'withholding_payment': True
                        })
                payment_value_list = [payment_vals]
                payments = self.env['account.payment'].create(
                    payment_value_list)
                pay_dict[payments] = list(
                    filter(lambda l: l.move_id.name == payments.memo,
                           to_reconcile))[0]
            for payment, line in pay_dict.items():
                payment.action_post()
                if payment.name == "/":
                    payment.name = payment.move_id.name
                payment.action_validate()
                domain = [
                    ('account_type', 'in', ('asset_receivable', 'liability_payable')),
                    ('reconciled', '=', False)]
                payment_lines = payment.move_id.line_ids.filtered_domain(domain)
                for account in payment_lines.account_id:
                    (payment_lines + line).filtered_domain(
                        [('account_id', '=', account.id),
                         ('reconciled', '=', False)]).reconcile()
            if all([line.state == 'post' for line in
                    active_id.receipt_line_ids]):
                if active_id.name == _('New'):
                    active_id.name = active_id.env['ir.sequence'].next_by_code(
                        'lyg.account.receipt') or _('New')
                active_id.write({
                    'date': datetime.datetime.now(),
                })
                active_id.write({
                    'state': 'post',
                })


class InvoicePaymentLines(models.TransientModel):
    _name = 'payment.receipt.line'
    _description = 'Invoice Payment Lines'

    pay_inv_id = fields.Many2one('account.payment.wizard')
    invoice_id = fields.Many2one('account.move')
    payment_difference_handling = fields.Selection([('open', 'Keep open'),
                                                    ('reconcile',
                                                     'Mark as fully paid')],
                                                   default='open',
                                                   string="Payment Difference Handling")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company)
    company_currency_id = fields.Many2one('res.currency',
                                          string="Company Currency",
                                          related='company_id.currency_id')
    write_off_account_id = fields.Many2one('account.account',
                                           string="Difference Account",
                                           copy=False,
                                           domain="[('deprecated', '=', False)]")
    write_off_label = fields.Char(string='Journal Item Label',
                                  help='Change label of the counterpart that will hold the payment difference')
    payment_diff = fields.Float("Payment Difference",
                                compute="_compute_amount_payment_diff",
                                store=False)

    @api.depends('pay_inv_id.remain_amount')
    def _compute_amount_payment_diff(self):
        """Function call to compute diff of payment and invoice amount."""
        remain_amount = eval(self.pay_inv_id.remain_amount)
        for line in self:
            payment_diff = line.invoice_id.amount_residual - remain_amount.get(
                line.invoice_id.id, 0)
            line.payment_diff = payment_diff

    @api.onchange('payment_difference_handling')
    def onchange_payment_difference_handling(self):
        for rec in self:
            if rec.payment_difference_handling == 'open':
                rec.write_off_label = False
            else:
                rec.write_off_label = 'Write-Off'
