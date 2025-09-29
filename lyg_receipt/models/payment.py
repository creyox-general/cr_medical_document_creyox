#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################

from odoo import fields, models, api, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
import datetime


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    receipt_id = fields.Many2one('lyg.account.receipt', copy=False)
    withholding_payment = fields.Boolean()
    code = fields.Char(related='company_id.account_fiscal_country_id.code',
                       string="Code-Country")
    means_of_payment = fields.Selection(
        [('1', 'Cash'), ('2', 'Check'), ('3', 'Credit Card'),
         ('4', 'Bank Transfer'), ('5', 'Gift Card'), ('6', 'Return Note'),
         ('7', 'Promissory Note'), ('8', 'Standing Order'), ('9', 'Other')],
        default='1')
    lyg_check_number = fields.Char()
    bank_number = fields.Char('Bank Number')
    branch_number = fields.Char('Branch Number')
    account_number = fields.Char('Account Number')
    check_payment_due_date = fields.Date('Check/Credit Pay Due Date')
    validity_date = fields.Date("Validity Date")

    def write(self, vals):
        # Override to restrict customer payment creation
        res = super().write(vals)
        for rec in self:
            if rec.partner_type == 'customer' and self._context.get(
                    'customer_payment') and 'is_deposited' not in vals:
                raise UserError(
                    _("""You can not create or edit customer payment, Please create receipt for this payment..!!"""))
        return res

    def get_reconcile_ids(self, payments):
        query = f'''
                SELECT
                    payment.id,
                    ARRAY_AGG(DISTINCT invoice.id) AS invoice_ids,
                    invoice.move_type
                FROM account_payment payment
                JOIN account_move move ON move.id = payment.move_id
                JOIN account_move_line line ON line.move_id = move.id
                JOIN account_partial_reconcile part ON
                    part.debit_move_id = line.id
                    OR
                    part.credit_move_id = line.id
                JOIN account_move_line counterpart_line ON
                    part.debit_move_id = counterpart_line.id
                    OR
                    part.credit_move_id = counterpart_line.id
                JOIN account_move invoice ON invoice.id = counterpart_line.move_id
                JOIN account_account account ON account.id = line.account_id
                WHERE account.account_type IN ('asset_receivable', 'liability_payable')
                    AND payment.id = {payments.id}
                    AND line.id != counterpart_line.id
                    AND invoice.move_type in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt')
                GROUP BY payment.id, invoice.move_type
            '''
        self._cr.execute(query)
        query_res = self._cr.dictfetchall()
        return query_res

    def create_receipt(self, payments):
        # Function used to create receipt
        payments._compute_stat_buttons_from_reconciliation()
        res = self.get_reconcile_ids(payments)
        invoice_id = self.env['account.move'].browse(
            res[0].get('invoice_ids', [])) if res else payments[0].invoice_ids
        name = ''
        if not self.company_id._fields.get('is_tranzila_document',
                                           False) or not self.company_id._fields.get(
            'is_greeninvoice_document',
            False) or not self.company_id._fields.get('is_i4u_document',
                                                      False):
            name = self.env['ir.sequence'].next_by_code(
                'lyg.account.receipt') or _('New')
        if payments[0].payment_transaction_id.npay and payments[0].payment_transaction_id.fpay\
                and payments[0].payment_transaction_id.spay:
            payments[0].npay = payments[0].payment_transaction_id.npay
            payments[0].fpay = payments[0].payment_transaction_id.fpay
            payments[0].spay = payments[0].payment_transaction_id.spay
        rec_vals = {
            'name': name,
            'receipt_user_id': False,
            'partner_id': invoice_id.partner_id.id if invoice_id else payments[0].partner_id.id,
            'company_id': payments[0].company_id.id,
            'date': datetime.datetime.now(),
            'currency_id': invoice_id.currency_id.id if invoice_id else self.company_id.currency_id.id,
            'subject': "תשלום מקוון" if payments[
                0].payment_transaction_id else "",
            'receipt_line_ids': [
                (0, 0, {'journal_id': payment.journal_id.id,
                        'type': 'invoice' if invoice_id else 'generic',
                        'invoice_id': invoice_id.id if invoice_id else None,
                        'invoice_amount': payment.reconciled_invoice_ids[
                            0].amount_residual if payment.reconciled_invoice_ids else 0.0,
                        'tranzila_npay': payment.payment_transaction_id.npay,
                        'tranzila_spay': payment.payment_transaction_id.spay,
                        'tranzila_fpay': payment.payment_transaction_id.fpay,
                        'amount': payment.amount,
                        'means_of_payment': '3'}) for payment
                in payments]
        }
        receipt_id = self.env['lyg.account.receipt'].with_context(
            wizard_payment=True).create(rec_vals)
        payments.write({'receipt_id': receipt_id.id, 'means_of_payment': '3'})
        receipt_id.write({'state': 'post'})
        return receipt_id


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _create_payment(self, **extra_create_values):
        res = super(PaymentTransaction, self)._create_payment()
        template_id = self.env.ref('lyg_receipt.lyg_mail_template_receipt')
        if self._context and not self._context.get('lastcall'):
            if res.partner_type == 'customer' and res.company_id.account_fiscal_country_id.code == 'IL':
                if res:
                    receipt = res.with_user(SUPERUSER_ID).create_receipt(res)
                    if receipt.company_id.send_an_email_receipts and (
                            not res.company_id._fields.get('is_tranzila_document',
                                                           False) or not res.company_id._fields.get(
                            'is_greeninvoice_document',
                            False) or not res.company_id._fields.get(
                            'is_i4u_document', False)):
                        template_id.sudo().with_user(SUPERUSER_ID).send_mail(
                            receipt.id, force_send=True)
        return res
