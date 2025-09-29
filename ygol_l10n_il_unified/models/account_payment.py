import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    credit_transaction_type = fields.Selection(
        [
            ("1", "Regular"),
            ("2", "Payments"),
            ("3", "Credit"),
            ("4", "Decline Payment"),
            ("5", "Others"),
        ],
        string="Credit transaction type",
    )
    credit_card_name = fields.Char("Credit Card name")
    comp_code_clears = fields.Selection(
        [
            ("1", "Isracard"),
            ("2", "CAL"),
            ("3", "Diners"),
            ("4", "American Express"),
            ("5", "Leumi Card"),
        ],
        "Code Clearing company",
    )
    # bank_number = fields.Char('Bank Number')
    # branch_number = fields.Char('Branch Number')
    # account_number = fields.Char('Account Number')
    # check_payment_due_date = fields.Date('Check/Credit Pay Due Date')


# class AccountLYGReceipt(models.Model):
#
#     _inherit = "lyg.account.receipt"
#
#     def action_post_receipt(self):
#         """Function call to create payment and redirect to wizard."""
#         remain_amount = self.remain_amount and eval(self.remain_amount) or {}
#         if not self.receipt_line_ids:
#             raise ValidationError(
#                 _("You can't confirm Receipt without Payment Lines."))
#         for line in self.receipt_line_ids:
#             if line.type == 'generic' and line.state != 'post':
#                 self.generic_payment_receipt(line)
#         if all([line.type == 'generic' and line.state == 'post' for line in self.receipt_line_ids]):
#             self.write({
#                 'state': 'post'
#             })
#             if self.name == _('New'):
#                 self.name = self.env['ir.sequence'].next_by_code('lyg.account.receipt') or _('New')
#         if any([line.type == 'invoice' for line in self.receipt_line_ids]):
#             _logger.info("\n\n -------IN ALL INVOICE CONDITION------- :\n%s", self.receipt_line_ids)
#             total_unpaid = self.receipt_line_ids.mapped('invoice_id.amount_residual')
#             total_line_invoice_ids = self.receipt_line_ids.mapped('invoice_id')
#             calculated_remain_amount = {inv.id: value for inv, value in zip(total_line_invoice_ids, total_unpaid)}
#             _logger.info("\n\n -------IN ALL INVOICE calculated_remain_amount------- :\n%s", calculated_remain_amount)
#             if all(remain_amount.get(key, 0) == value for key, value in calculated_remain_amount.items()):
#                 _logger.info("\n\n -------IN ALL INVOICE calculated_remain_amount------- :\n%s",
#                             self.receipt_line_ids)
#                 dict_len = eval(self.remain_amount)
#                 to_reconcile = []
#                 batches = self._get_payment_lines()
#                 if len(dict_len) > 1:
#                     new_batches = []
#                     for batch_result in batches:
#                         for line_move in batch_result['lines']:
#                             new_batches.append({
#                                 **batch_result,
#                                 'lines': line_move,
#                             })
#                     batches = new_batches
#                 for batch_result in batches:
#                     to_reconcile.append(batch_result['lines'])
#                 pay_dict = {}
#                 for line in self.receipt_line_ids.filtered(lambda l: l.type == 'invoice'):
#                     line.write({'state': 'post'})
#                     # append lines in it
#                     # payment values for open and write-off
#                     payment_vals = {
#                         'date': self.date,
#                         'amount': line.amount,
#                         'payment_type': 'inbound',
#                         'partner_type': 'customer',
#                         'ref': line.invoice_id.name,
#                         'currency_id': self.currency_id.id,
#                         'journal_id': line.journal_id.id,
#                         'partner_id': self.partner_id.id,
#                         'receipt_id': self.id,
#                         'means_of_payment': line.means_of_payment or False,
#                         'bank_number': line.bank,
#                         'branch_number': line.branch,
#                         'account_number': line.credit_account_no,
#                         'lyg_check_number': line.voucher_check_no
#                     }
#                     if self.company_id.withholding_tax_process:
#                         if line.withholding_amount:
#                             # Append Write Off
#                             payment_vals['withholding_line_vals'] = {
#                                 'name': 'Withholding Payment',
#                                 'amount': line.withholding_amount,
#                                 'account_id': self.company_id.cust_withholding_tax_account_id.id,
#                                 'withholding_tax_process': True,
#
#                             }
#                             payment_vals.update({
#                                 'withholding_payment': True
#                             })
#                     payment_value_list = [payment_vals]
#                     payments = self.env['account.payment'].create(payment_value_list)
#                     pay_dict[payments] = list(filter(lambda l: l.move_id.name == payments.ref, to_reconcile))[0]
#                 for payment, line in pay_dict.items():
#                     payment.action_post()
#                     domain = [('account_internal_type', 'in', ('receivable', 'payable')), ('reconciled', '=', False)]
#                     payment_lines = payment.line_ids.filtered_domain(domain)
#                     for account in payment_lines.account_id:
#                         (payment_lines + line).filtered_domain(
#                             [('account_id', '=', account.id), ('reconciled', '=', False)]).reconcile()
#                 if all([line.state == 'post' for line in self.receipt_line_ids]):
#                     if self.name == _('New'):
#                         self.name = self.env['ir.sequence'].next_by_code('lyg.account.receipt') or _('New')
#                     self.write({
#                         'state': 'post',
#                     })
#             else:
#                 return {
#                     'name': _('Register Payment'),
#                     'res_model': 'account.payment.wizard',
#                     'view_mode': 'form',
#                     'context': {
#                         'active_model': 'account.payment.wizard',
#                         'active_ids': self.id,
#                         'default_remain_amount': self.remain_amount,
#                     },
#                     'target': 'new',
#                     'type': 'ir.actions.act_window',
#                 }
