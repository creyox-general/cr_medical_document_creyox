#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################

from odoo import models, fields, api, _, Command
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    withtholding_amount = fields.Monetary("Withholding Amount", store=True,
                                          currency_field='currency_id')
    withholding_tax_process = fields.Boolean(
        related="company_id.withholding_tax_process")

    amount_after_withholding = fields.Monetary("Amount After Withholding",
                                               copy=False,
                                               store=True,
                                               compute="_compute_amount_after_withholding",
                                               currency_field='currency_id')

    @api.depends('withtholding_amount', 'amount')
    def _compute_amount_after_withholding(self):
        for payment in self:
            new_value = payment.amount - payment.withtholding_amount
            if payment.amount_after_withholding != new_value:
                payment.amount_after_withholding = new_value

    def update_amount_after_withholding_cron(self):
        """Cron job to update amount_after_withholding for all records."""
        payments = self.env['account.payment'].search([])
        for payment in payments:
            new_value = payment.amount - payment.withtholding_amount
            if payment.amount_after_withholding != new_value:
                payment.amount_after_withholding = new_value

    def _cron_calculate_withholding_amount(self):
        """
        Calculate the withholding amount in payments
        """
        payments = self.env['account.payment'].search([])
        account_codes = ['111200', '111230']
        for payment in payments:
            move_lines = payment.move_id.line_ids.filtered(
                lambda line: line.account_id.code in account_codes
            )
            payment.withtholding_amount = (sum(move_lines.mapped('credit')) +
                                       sum(move_lines.mapped('debit')))

    @api.model_create_multi
    def create(self, vals_list):
        company_ids = self.env['res.company'].search(
            [('account_fiscal_country_id.code', '=', 'IL'),
             ('withholding_tax_process', '=', True)])
        for company_id in company_ids:
            if company_id.id == self.env.company.id:
                withholding = False
                for vals in vals_list:
                    partner_id = self.env['res.partner'].browse(vals.get(
                        'partner_id')) if vals.get('partner_id') else False
                    if vals.get(
                            'partner_type') == 'supplier' and partner_id and partner_id.country_id.code == 'IL':
                        withholding = True
                    elif (vals.get('partner_type') == 'customer' and
                          vals.get('withtholding_amount')):
                        withholding = True
                    elif vals.get('receipt_id') and vals.get(
                            'withholding_payment'):
                        withholding = True
                    elif (vals.get('is_hmk_payment') and
                          vals.get('hmk_withholding_payment')):
                        withholding = True
                if withholding:
                    write_off_line_vals_list = []
                    for vals in vals_list:
                        withholding_line_vals_list = []
                        # Hack to add a custom write-off line.
                        write_off_line_vals_list.append(
                            vals.pop('write_off_line_vals', None))
                        if 'withholding_line_vals' in vals:
                            withholding_line_vals_list.append(
                                vals.pop('withholding_line_vals', None))
                        # Force the move_type to avoid inconsistency with residual 'default_move_type' inside the context.
                        # vals['payment_type'] = 'outbound'

                        # Force the computation of 'journal_id' since this field is set on account.move but must have the
                        # bank/cash type.
                        if 'journal_id' not in vals:
                            vals['journal_id'] = self._get_default_journal().id

                        # Since 'currency_id' is a computed editable field, it will be computed later.
                        # Prevent the account.move to call the _get_default_currency method that could raise
                        # the 'Please define an accounting miscellaneous journal in your company' error.
                        if 'currency_id' not in vals:
                            journal = self.env['account.journal'].browse(
                                vals['journal_id'])
                            vals[
                                'currency_id'] = journal.currency_id.id or journal.company_id.currency_id.id
                    payments = super(models.Model, self).create(vals_list)

                    for i, pay in enumerate(payments):
                        write_off_line_vals = write_off_line_vals_list[i]
                        withholding_line_vals = {}
                        if withholding_line_vals_list:
                            withholding_line_vals = withholding_line_vals_list[i]
                        # Write payment_id on the journal entry plus the fields being stored in both models but having the same
                        # name, e.g. partner_bank_id. The ORM is currently not able to perform such synchronization and make things
                        # more difficult by creating related fields on the fly to handle the _inherits.
                        # Then, when partner_bank_id is in vals, the key is consumed by account.payment but is never written on
                        # account.move.
                        to_write = {'payment_ids': Command.link(pay.id)}
                        for k, v in vals_list[i].items():
                            if k in self._fields and self._fields[
                                k].store and k in pay.move_id._fields and \
                                    pay.move_id._fields[k].store:
                                to_write[k] = v
                        if 'line_ids' not in vals_list[i]:
                            to_write['line_ids'] = [(0, 0, line_vals) for line_vals in
                                                    pay._prepare_move_line_default_vals(
                                                        write_off_line_vals=write_off_line_vals,
                                                        withholding_line_vals=withholding_line_vals)]
                        if pay.receipt_id and pay.withholding_payment:
                            pay._generate_journal_entry(
                                force_balance=None,
                                line_ids=to_write['line_ids'])
                    return payments
        return super(AccountPayment, self).create(vals_list)

    def get_withholding_condition(self):
        # Condition added to check supplier type payment
        withholding = False
        for rec in self:
            if rec.partner_type == 'supplier' and rec.partner_id.country_id.code == 'IL':
                withholding = True
            # Condition added to check receipt payment
            elif rec.receipt_id and rec.withholding_payment:
                withholding = True
            # Condition added to check HMK Payment
            elif rec._fields.get('is_hmk_payment',
                                  False) and rec.is_hmk_payment and rec.hmk_withholding_payment:
                withholding = True
            # Condition added to check customer type payment(From the invoice only)
            elif rec.partner_type == 'customer' and rec.withtholding_amount:
                withholding = True
            else:
                withholding = False
            return withholding

    def _generate_journal_entry(self, write_off_line_vals=None, force_balance=None, line_ids=None, withholding_balance=None):
        withholding = self.get_withholding_condition()
        if self.company_id.withholding_tax_process and withholding:
            need_move = self.filtered(lambda p: not p.move_id and p.outstanding_account_id)
            assert len(self) == 1 or (not write_off_line_vals and not force_balance and not line_ids and not withholding_balance)


            move_vals = []
            for pay in need_move:
                move_vals.append({
                    'move_type': 'entry',
                    'ref': pay.memo,
                    'date': pay.date,
                    'journal_id': pay.journal_id.id,
                    'company_id': pay.company_id.id,
                    'partner_id': pay.partner_id.id,
                    'currency_id': pay.currency_id.id,
                    'partner_bank_id': pay.partner_bank_id.id,
                    'line_ids': line_ids or [
                        Command.create(line_vals)
                        for line_vals in pay._prepare_move_line_default_vals(
                            write_off_line_vals=write_off_line_vals,
                            force_balance=force_balance,
                        )
                    ],
                    'origin_payment_id': pay.id,
                })
            moves = self.env['account.move'].create(move_vals)

            for pay, move in zip(need_move, moves):
                pay.write(
                    {'move_id': move.id,
                     'state': 'paid',
                     'name': move.name}
                )

        return super(AccountPayment, self)._generate_journal_entry(write_off_line_vals, force_balance, line_ids)

    def get_withholding_tax_rate(self):
        """Function call to get withholding tax (%) based on company and validity date."""
        withholding_tax_rate = 0.0
        # import pdb; pdb.set_trace()
        split_memo = self.memo
        ref = split_memo.split(" ")
        bill = self.env['account.move'].search([('ref', '=', self.memo),
                                                ('move_type', '=',
                                                 'in_invoice')],limit=1)
        invoice = self.env['account.move'].search([('ref', '=', self.memo),
                                                   ('move_type', '=',
                                                    'out_invoice')],limit=1)
        date = bill.invoice_date if bill else invoice.invoice_date if invoice else self.date if len(
            ref) > 1 else None
        if self.partner_id.country_id.code == 'IL':
            if self.partner_id.withholding_tax_rate:
                if (self.partner_id.valid_until_date and
                        self.partner_id.valid_until_date > date) if date \
                        else self.date:
                    withholding_tax_rate = self.partner_id.withholding_tax_rate
            else:
                if (self.partner_id.valid_until_date and
                        self.partner_id.valid_until_date > date) if date \
                        else self.date:
                    withholding_tax_rate = self.company_id.def_withholding_tax_rate
            return withholding_tax_rate


    def _seek_for_lines(self):
        ''' Helper used to dispatch the journal items between:
        - The lines using the temporary liquidity account.
        - The lines using the counterpart account.
        - The lines being the write-off lines.
        :return: (liquidity_lines, counterpart_lines, writeoff_lines)
        '''
        withholding = self.get_withholding_condition()
        if self.company_id.withholding_tax_process and withholding:
            self.ensure_one()
            liquidity_lines = self.env['account.move.line']
            counterpart_lines = self.env['account.move.line']
            writeoff_lines = self.env['account.move.line']
            # withholding_tax_line for new journal entry line
            withholding_tax_line = self.env['account.move.line']
            for line in self.move_id.line_ids:
                if line.account_id in self._get_valid_liquidity_accounts():
                    liquidity_lines += line
                elif line.account_id.account_type in ('asset_receivable',
                                                      'liability_payable') or line.partner_id == line.company_id.partner_id:
                    counterpart_lines += line
                # Added new condition to get withholding_tax_line from existing one.
                elif (
                        line.account_id == self.company_id.withholding_tax_account_id) or (
                        line.account_id == self.company_id.cust_withholding_tax_account_id):
                    withholding_tax_line += line
                else:
                    writeoff_lines += line
            # Modified return to return data with withholding_tax_line
            return liquidity_lines, counterpart_lines, writeoff_lines, withholding_tax_line
        return super(AccountPayment, self)._seek_for_lines()

    def _synchronize_to_moves(self, changed_fields):
        ''' Update the account.move regarding the modified account.payment.
        :param changed_fields: A list containing all modified fields on account.payment.
        '''

        withholding = self.get_withholding_condition()
        if self.company_id.withholding_tax_process and withholding:
            if self._context.get('skip_account_move_synchronization'):
                return

            if not any(field_name in changed_fields for field_name in (
                    'date', 'amount', 'payment_type', 'partner_type',
                    'payment_reference',
                    'currency_id', 'partner_id', 'destination_account_id',
                    'partner_bank_id',
            )):
                return

            for pay in self.with_context(
                    skip_account_move_synchronization=True):
                # Get withholding_tax_line from _seek_for_lines function
                liquidity_lines, counterpart_lines, writeoff_lines, withholding_tax_line = pay._seek_for_lines()

                # Make sure to preserve the write-off amount.
                # This allows to create a new payment with custom 'line_ids'.

                if writeoff_lines:
                    counterpart_amount = sum(
                        counterpart_lines.mapped('amount_currency'))
                    writeoff_amount = sum(
                        writeoff_lines.mapped('amount_currency'))

                    # To be consistent with the payment_difference made in account.payment.register,
                    # 'writeoff_amount' needs to be signed regarding the 'amount' field before the write.
                    # Since the write is already done at this point, we need to base the computation on accounting values.
                    if (counterpart_amount > 0.0) == (writeoff_amount > 0.0):
                        sign = -1
                    else:
                        sign = 1
                    writeoff_amount = abs(writeoff_amount) * sign

                    write_off_line_vals = {
                        'name': writeoff_lines[0].name,
                        'amount': writeoff_amount,
                        'account_id': writeoff_lines[0].account_id.id,
                    }
                else:
                    write_off_line_vals = {}

                line_vals_list = pay._prepare_move_line_default_vals(
                    write_off_line_vals=write_off_line_vals)
                # append withholding_tax_line related changes val
                line_ids_commands = [
                    (1, liquidity_lines.id, line_vals_list[0]),
                    (1, counterpart_lines.id, line_vals_list[1]),
                    (1, withholding_tax_line.id, line_vals_list[2])
                ]
                for line in writeoff_lines:
                    line_ids_commands.append((2, line.id))
                # restrict to append new line
                for extra_line_vals in line_vals_list[3:]:
                    line_ids_commands.append((0, 0, extra_line_vals))
                # Update the existing journal items.
                # If dealing with multiple write-off lines, they are dropped and a new one is generated.
                pay.move_id.write({
                    'partner_id': pay.partner_id.id,
                    'currency_id': pay.currency_id.id,
                    'partner_bank_id': pay.partner_bank_id.id,
                    'line_ids': line_ids_commands,
                })

        else:
            super(AccountPayment, self)._synchronize_to_moves(changed_fields)

    def _prepare_move_line_default_vals(self, write_off_line_vals=None,
                                        withholding_line_vals=None,
                                        force_balance=None):
        # Condition added for calculating withholding amount
        withholding = self.get_withholding_condition()
        if self.company_id.withholding_tax_process and withholding:
            self.ensure_one()
            write_off_line_vals = write_off_line_vals or {}

            if not self.outstanding_account_id:
                raise UserError(_(
                    "You can't create a new payment without an outstanding payments/receipts account set either on the company or the %s payment method in the %s journal.",
                    self.payment_method_line_id.name,
                    self.journal_id.display_name))
            # Withholding amount and line name
            write_off_amount_currency = sum(
                x['amount_currency'] for x in write_off_line_vals)
            # Compute amounts.
            withholding_taxamount_currency = 0.0
            if self.partner_type == 'supplier':
                withholding_tax_rate = self.get_withholding_tax_rate()
                # Raised warning if tax rate not set at partner
                withholding_taxamount_currency = - round((
                        self.amount * withholding_tax_rate / 100), 2)
                self.withtholding_amount = round((
                        self.amount * withholding_tax_rate / 100), 2)
                if self.payment_type == 'inbound':
                    # Receive money.
                    liquidity_amount_currency = self.amount
                elif self.payment_type == 'outbound':
                    # Send money.
                    # Modified amount of liquidity
                    liquidity_amount_currency = -self.amount - withholding_taxamount_currency
                    write_off_amount_currency *= -1
                else:
                    liquidity_amount_currency = write_off_amount_currency = 0.0
            elif withholding_line_vals:
                withholding_line_vals = withholding_line_vals or {}
                self.withtholding_amount = withholding_line_vals.get(
                    'amount', 0.0) if self.receipt_id.is_credit_receipt else withholding_line_vals.get(
                    'amount', 0.0)
                withholding_taxamount_currency = - withholding_line_vals.get(
                    'amount', 0.0) if self.receipt_id.is_credit_receipt else withholding_line_vals.get(
                    'amount', 0.0)
                if self.payment_type == 'inbound':
                    # Receive money.
                    liquidity_amount_currency = self.amount
                elif self.payment_type == 'outbound':
                    # Send money.
                    liquidity_amount_currency = - (self.amount) if self.receipt_id.is_credit_receipt else -(
                            self.amount - withholding_taxamount_currency)
                    write_off_amount_currency *= -1
                else:
                    liquidity_amount_currency = write_off_amount_currency = 0.0
            else:
                if self.payment_type == 'inbound':
                    # Receive money.
                    liquidity_amount_currency = self.amount
                elif self.payment_type == 'outbound':
                    # Send money.
                    liquidity_amount_currency = -self.amount
                    write_off_amount_currency *= -1
                else:
                    liquidity_amount_currency = write_off_amount_currency = 0.0
            write_off_balance = self.currency_id._convert(
                write_off_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
            liquidity_balance = self.currency_id._convert(
                liquidity_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
            # withholding amount currency.
            withholding_tax_balance = self.currency_id._convert(
                withholding_taxamount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
            # Modified counterpart_amount_currency and counterpart_balance with withholding_taxamount
            counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency - withholding_taxamount_currency
            counterpart_balance = -liquidity_balance - write_off_balance - withholding_taxamount_currency
            currency_id = self.currency_id.id

            if self.payment_type == 'inbound':
                liquidity_line_name = _('Transfer to %s',
                                        self.journal_id.name)
            else:  # payment.payment_type == 'outbound':
                liquidity_line_name = _('Transfer from %s',
                                        self.journal_id.name)

            liquidity_line_name = self.payment_reference

            # Compute a default label to set on the journal items.

            payment_display_name = {
                'outbound-customer': _("Customer Reimbursement"),
                'inbound-customer': _("Customer Payment"),
                'outbound-supplier': _("Vendor Payment"),
                'inbound-supplier': _("Vendor Reimbursement"),
            }

            default_line_name = self.env[
                'account.move.line']._get_default_line_name(
                _("Internal Transfer") if self.paired_internal_transfer_payment_id else
                payment_display_name[
                    '%s-%s' % (self.payment_type, self.partner_type)],
                self.amount,
                self.currency_id,
                self.date,
                partner=self.partner_id,
            )
            # Line vals list modified with wothholding tax dict
            line_vals_list = [
                # Liquidity line.
                {
                    'name': liquidity_line_name or default_line_name,
                    'date_maturity': self.date,
                    'amount_currency': liquidity_amount_currency,
                    'currency_id': currency_id,
                    'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                    'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.outstanding_account_id.id,
                },
                # Receivable / Payable.
                {
                    'name': self.payment_reference or default_line_name,
                    'date_maturity': self.date,
                    'amount_currency': counterpart_amount_currency,
                    'currency_id': currency_id,
                    'debit': round(counterpart_balance,
                                   2) if counterpart_balance > 0.0 else 0.0,
                    'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.destination_account_id.id,
                },
            ]
            if self.partner_type == 'supplier':
                # Withholding amount line.
                line_vals_list.append({
                    'name': default_line_name,
                    'date_maturity': self.date,
                    'amount_currency': withholding_taxamount_currency,
                    'currency_id': currency_id,
                    'debit': withholding_tax_balance if withholding_tax_balance > 0.0 else 0.0,
                    'credit': -withholding_tax_balance if withholding_tax_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.company_id.withholding_tax_account_id.id,
                })
            if withholding_line_vals:
                line_vals_list.append({
                    'name': withholding_line_vals.get(
                        'name') or default_line_name,
                    'date_maturity': self.date,
                    'amount_currency': withholding_taxamount_currency,
                    'currency_id': currency_id,
                    'debit': withholding_tax_balance if withholding_tax_balance > 0.0 else 0.0,
                    'credit': -withholding_tax_balance if withholding_tax_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': withholding_line_vals.get('account_id'),
                })
            if not self.currency_id.is_zero(write_off_amount_currency):
                # Write-off line.
                name = next(
                    (x['name'] for x in write_off_line_vals if 'name' in x),
                    default_line_name)
                account_id = next(
                    (x['account_id'] for x in write_off_line_vals if
                     'account_id' in x), None)
                line_vals_list.append({
                    'name': name,
                    'amount_currency': write_off_amount_currency,
                    'currency_id': currency_id,
                    'debit': write_off_balance if write_off_balance > 0.0 else 0.0,
                    'credit': -write_off_balance if write_off_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': account_id,
                })
            return line_vals_list
        else:
            return super(AccountPayment, self)._prepare_move_line_default_vals(
                write_off_line_vals=write_off_line_vals,force_balance=force_balance)

    @api.depends('move_id.line_ids.amount_residual',
                 'move_id.line_ids.amount_residual_currency',
                 'move_id.line_ids.account_id')
    def _compute_reconciliation_status(self):
        ''' Compute the field indicating if the payments are already reconciled with something.
        This field is used for display purpose (e.g. display the 'reconcile' button redirecting to the reconciliation
        widget).'''
        # withholding_lines_data = self.filtered(
        #     lambda w : w.partner_type == 'supplier' and w.partner_id.country_id.code == 'IL' and w.withholding_tax_process or ('receipt_id' in w._fields and w.receipt_id and w.withholding_payment))
        withholding_lines_data = self.filtered(lambda
                                                   w: w.get_withholding_condition() and w.company_id.withholding_tax_process)
        super(AccountPayment,
              self - withholding_lines_data)._compute_reconciliation_status()
        # Override function to add withholding_tax_line as we changed _seek_for_lines for withholding line.
        for pay in withholding_lines_data:
            # Get withholding_tax_line from _seek_for_lines function
            liquidity_lines, counterpart_lines, writeoff_lines, withholding_tax_line = pay._seek_for_lines()
            if not pay.currency_id or not pay.id:
                pay.is_reconciled = False
                pay.is_matched = False
            elif pay.currency_id.is_zero(pay.amount):
                pay.is_reconciled = True
                pay.is_matched = True
            else:
                residual_field = 'amount_residual' if pay.currency_id == pay.company_id.currency_id else 'amount_residual_currency'
                if pay.journal_id.default_account_id and pay.journal_id.default_account_id in liquidity_lines.account_id:
                    # Allow user managing payments without any statement lines by using the bank account directly.
                    # In that case, the user manages transactions only using the register payment wizard.
                    pay.is_matched = True
                else:
                    pay.is_matched = pay.currency_id.is_zero(
                        sum(liquidity_lines.mapped(residual_field)))
                reconcile_lines = (
                            counterpart_lines + writeoff_lines + withholding_tax_line).filtered(
                    lambda line: line.account_id.reconcile)
                pay.is_reconciled = pay.currency_id.is_zero(
                    sum(reconcile_lines.mapped(residual_field)))

    def action_open_manual_reconciliation_widget(self):
        ''' Open the manual reconciliation widget for the current payment.
        :return: A dictionary representing an action.
        '''
        withholding = self.get_withholding_condition()
        if self.company_id.withholding_tax_process and withholding:
            self.ensure_one()
            if not self.partner_id:
                raise UserError(
                    _("Payments without a customer can't be matched"))
            liquidity_lines, counterpart_lines, writeoff_lines, withholding_tax_line = self._seek_for_lines()
            action_context = {'company_ids': self.company_id.ids,
                              'partner_ids': self.partner_id.ids}
            if self.partner_type == 'customer':
                action_context.update({'mode': 'customers'})
            elif self.partner_type == 'supplier':
                action_context.update({'mode': 'suppliers'})
            if counterpart_lines:
                action_context.update(
                    {'move_line_id': counterpart_lines[0].id})

            return {
                'type': 'ir.actions.client',
                'tag': 'manual_reconciliation_view',
                'context': action_context,
            }
        else:
            super(AccountPayment,
                  self).action_open_manual_reconciliation_widget()

    def _synchronize_from_moves(self, changed_fields):
        ''' Update the account.payment regarding its related account.move.
        Also, check both models are still consistent.
        :param changed_fields: A set containing all modified fields on account.move.
        '''
        if self.company_id.withholding_tax_process:
            if self._context.get('skip_account_move_synchronization'):
                return

            for pay in self.with_context(
                    skip_account_move_synchronization=True):

                # After the migration to 14.0, the journal entry could be shared between the account.payment and the
                # account.bank.statement.line. In that case, the synchronization will only be made with the statement line.
                if pay.move_id.statement_line_id:
                    continue

                move = pay.move_id
                move_vals_to_write = {}
                payment_vals_to_write = {}

                if 'journal_id' in changed_fields:
                    if pay.journal_id.type not in ('bank', 'cash'):
                        raise UserError(
                            _("A payment must always belongs to a bank or cash journal."))

                if 'line_ids' in changed_fields:
                    all_lines = move.line_ids
                    withholding = pay.get_withholding_condition()
                    withholding_amount = 0.0
                    if withholding:
                        liquidity_lines, counterpart_lines, writeoff_lines, withholding_tax_line = pay._seek_for_lines()
                        for tax_line in withholding_tax_line:
                            withholding_amount = tax_line.amount_currency
                    else:
                        liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()
                    if len(liquidity_lines) != 1:
                        raise UserError(_(
                            "Journal Entry %s is not valid. In order to proceed, the journal items must "
                            "include one and only one outstanding payments/receipts account.",
                            move.display_name,
                        ))

                    if len(counterpart_lines) != 1:
                        raise UserError(_(
                            "Journal Entry %s is not valid. In order to proceed, the journal items must "
                            "include one and only one receivable/payable account (with an exception of "
                            "internal transfers).",
                            move.display_name,
                        ))

                    if writeoff_lines and len(writeoff_lines.account_id) != 1:
                        raise UserError(_(
                            "Journal Entry %s is not valid. In order to proceed, "
                            "all optional journal items must share the same account.",
                            move.display_name,
                        ))

                    if any(line.currency_id != all_lines[0].currency_id for
                           line in all_lines):
                        raise UserError(_(
                            "Journal Entry %s is not valid. In order to proceed, the journal items must "
                            "share the same currency.",
                            move.display_name,
                        ))

                    if any(line.partner_id != all_lines[0].partner_id for line
                           in all_lines):
                        raise UserError(_(
                            "Journal Entry %s is not valid. In order to proceed, the journal items must "
                            "share the same partner.",
                            move.display_name,
                        ))

                    if counterpart_lines.account_id.account_type == 'asset_receivable':
                        partner_type = 'customer'
                    else:
                        partner_type = 'supplier'

                    liquidity_amount = liquidity_lines.amount_currency

                    move_vals_to_write.update({
                        'currency_id': liquidity_lines.currency_id.id,
                        'partner_id': liquidity_lines.partner_id.id,
                    })
                    payment_vals_to_write.update({
                        'amount': abs(liquidity_amount),
                        'withtholding_amount': abs(withholding_amount) or 0.0,
                        'partner_type': partner_type,
                        'currency_id': liquidity_lines.currency_id.id,
                        'destination_account_id': counterpart_lines.account_id.id,
                        'partner_id': liquidity_lines.partner_id.id,
                    })
                    if liquidity_amount > 0.0:
                        payment_vals_to_write.update(
                            {'payment_type': 'inbound'})
                    elif liquidity_amount < 0.0:
                        payment_vals_to_write.update(
                            {'payment_type': 'outbound'})

                move.write(
                    move._cleanup_write_orm_values(move, move_vals_to_write))
                pay.write(
                    move._cleanup_write_orm_values(pay, payment_vals_to_write))

        else:
            super(AccountPayment, self)._synchronize_from_moves(changed_fields)


    @api.depends('invoice_ids.payment_state', 'move_id.line_ids.amount_residual')
    def _compute_state(self):
        for payment in self:
            withholding = payment.get_withholding_condition()
            if payment.company_id.withholding_tax_process and withholding:
                if not payment.state:
                    payment.state = 'draft'
                # in_process --> paid
                if payment.state == 'in_process' and payment.outstanding_account_id:
                    move = payment.move_id
                    values = payment._seek_for_lines()
                    if len(values) == 3:
                        liquidity, _counterpart, _writeoff = values
                    elif len(values) == 4:
                        liquidity, _counterpart, _writeoff, _withholding_tax_line = values
                    else:
                        super()._compute_state()
                        continue
                    if move and move.currency_id.is_zero(sum(liquidity.mapped('amount_residual'))):
                        payment.state = 'paid'
                        continue
                if payment.state == 'in_process' and payment.invoice_ids and all(invoice.payment_state == 'paid' for invoice in payment.invoice_ids):
                    payment.state = 'paid'
            else:
                return super(AccountPayment, payment)._compute_state()
