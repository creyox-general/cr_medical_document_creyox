#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.http import request
from hashlib import sha256
from json import dumps
import json
from odoo.tools import float_round
import logging
import datetime

_logger = logging.getLogger(__name__)

INTEGRITY_HASH_RECEIPT_FIELDS = ('date', 'invoice_id', 'company_id', 'partner_id', 'receipt_user_id')
INTEGRITY_HASH_LINE_FIELDS = ('amount', 'journal_id')


class AccountReceipt(models.Model):
    _name = 'lyg.account.receipt'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin',
                'sequence.mixin']
    _description = "Receipt"

    @api.depends('payment_ids')
    def _get_payment_count(self):
        """Function calculate payment for smart button."""
        self.payment_count = len(self.payment_ids)

    @api.depends('receipt_line_ids.amount')
    def _total_payment_amount(self):
        """Function calculate payment lines total amount"""
        for rec in self:
            rec.total_pay_amount = 0.0
            for line in rec.receipt_line_ids:
                rec.total_pay_amount += line.amount

    @api.depends('receipt_line_ids.withholding_amount')
    def _total_withholding_amount(self):
        """Function calculate payment lines total amount"""
        for rec in self:
            rec.payment_diff_tax_writeoff = 0.0
            for line in rec.receipt_line_ids:
                rec.payment_diff_tax_writeoff += line.withholding_amount

    @api.depends('currency_id', 'total_pay_amount')
    def _total_ils_amount(self):
        for rec in self:
            if rec.currency_id != rec.company_id.currency_id and rec.currency_id == self.env.ref(
                    'base.ILS'):
                rec.total_ils = rec.currency_id._convert(
                    rec.total_pay_amount, rec.currency_id, rec.company_id,
                    rec.date)
            else:
                rec.total_ils = 0.0

    name = fields.Char("Name", index=True, default=lambda x: _('New'),
                       copy=False, translate=True)
    date = fields.Date("Date of Document", default=fields.Date.context_today)
    partner_id = fields.Many2one("res.partner", "Customer", required=True)
    type = fields.Selection(
        [('invoice', 'Invoice'), ('generic', 'Generic')], "Type",
        default="generic")
    invoice_id = fields.Many2one('account.move', "Specific Invoice",
                                 copy=False,
                                 domain=[('move_type', '=', 'out_invoice'),
                                         ('amount_residual', '!=', 0.0)])
    currency_id = fields.Many2one("res.currency", "Currency", default=lambda
        self: self.env.company.currency_id)
    currency_code = fields.Char(related='currency_id.name',
                                string="Currency Code")
    receipt_line_ids = fields.One2many("lyg.account.receipt.line",
                                       "pay_receipt_id", "Payment Lines",
                                       states={'draft': [('readonly', False)]})
    state = fields.Selection(
        [('draft', 'Draft'), ('post', 'Posted')], "State", default="draft")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    payment_ids = fields.One2many("account.payment", "receipt_id")
    payment_count = fields.Integer("Payment Count",
                                   compute="_get_payment_count")
    total_pay_amount = fields.Monetary("Paid Amount",
                                       compute="_total_payment_amount",
                                       store=True,
                                       currency_field='currency_id',
                                       copy="False")
    total_ils = fields.Monetary("Total ILS", compute="_total_ils_amount",
                                store=True)
    invoice_amount = fields.Monetary("Unpaid Amount", copy=False,
                                     currency_field='currency_id')
    subject = fields.Char("Subject", translate=True)
    note = fields.Text("Note", translate=True)
    receipt_user_id = fields.Many2one('res.users', copy=False, tracking=True,
                                      string='Salesperson',
                                      default=lambda self: self.env.user)
    remain_amount = fields.Char()

    # ==== Hash Fields ====
    receipt_restrict_mode_hash_table = fields.Boolean(
        related="company_id.receipt_restrict_mode_hash",
        string="Lock Posted Receipts with Hash")
    receipt_secure_sequence_number = fields.Integer(
        string="Inalteralbility No Gap Sequence #", readonly=True,
        copy=False)
    receipt_inalterable_hash = fields.Char(string="Inalterability Hash",
                                           readonly=True, copy=False)
    receipt_string_to_hash = fields.Char(compute='_compute_string_to_hash',
                                         readonly=True)
    payment_diff_tax_writeoff = fields.Monetary("Tax deducted at source",
                                                compute="_total_withholding_amount")
    is_donation = fields.Boolean("Donation?")
    donation_text = fields.Text("Donation Receipt",
                                default="* התרומה מוכרת לצרכי מס הכנסה לפי סעיף 46")


    # ===== Hash Functions ======
    def _get_new_hash(self, secure_seq_number):
        """ Returns the hash to write on receipts when they get posted"""
        self.ensure_one()
        # get the only one exact previous move in the securisation sequence
        prev_receipt = self.search([
            ('state', '=', 'post'),
            ('company_id', '=', self.company_id.id),
            ('invoice_id', '=', self.invoice_id.id),
            ('receipt_secure_sequence_number', '!=', 0),
            ('receipt_secure_sequence_number', '=',
             int(secure_seq_number) - 1)])
        if prev_receipt and len(prev_receipt) != 1:
            raise UserError(
                _('An error occurred when computing the inalterability. Impossible to get the unique previous posted receipt.'))

        # build and return the hash
        return self._compute_hash(
            prev_receipt.receipt_inalterable_hash if prev_receipt else u'')

    def _compute_hash(self, previous_hash):
        """ Computes the hash of the browse_record given as self, based on the hash
        of the previous record in the company's securisation sequence given as parameter"""
        self.ensure_one()
        hash_string = sha256(
            (previous_hash + self.receipt_string_to_hash).encode('utf-8'))
        return hash_string.hexdigest()

    def _compute_string_to_hash(self):
        def _getattrstring(obj, field_str):
            field_value = obj[field_str]
            if obj._fields[field_str].type == 'many2one':
                field_value = field_value.id
            return str(field_value)

        for rec in self:
            values = {}
            for field in INTEGRITY_HASH_RECEIPT_FIELDS:
                values[field] = _getattrstring(rec, field)

            for line in rec.receipt_line_ids:
                for field in INTEGRITY_HASH_LINE_FIELDS:
                    k = 'line_%d_%s' % (line.id, field)
                    values[k] = _getattrstring(line, field)
            # make the json serialization canonical
            #  (https://tools.ietf.org/html/draft-staykov-hu-json-canonical-form-00)
            rec.receipt_string_to_hash = dumps(values, sort_keys=True,
                                               ensure_ascii=True, indent=None,
                                               separators=(',', ':'))

    def write(self, vals):
        """Function call to generate new hash on receipt post"""
        has_been_posted = False
        for receipt in self:
            # write the hash and the secure_sequence_number when posting or invoicing an pos.order
            if ('state' in vals and vals.get('state') == 'post'):
                has_been_posted = True

            # restrict the operation in case we are trying to write a forbidden field
            if (('state' in vals and vals.get('state') == 'post') and set(
                    vals).intersection(
                    INTEGRITY_HASH_RECEIPT_FIELDS)):
                raise UserError(
                    _('According to the Goverment law, you cannot modify a receipt. Forbidden fields: %s.') % ', '.join(
                        INTEGRITY_HASH_RECEIPT_FIELDS))
            # restrict the operation in case we are trying to overwrite existing hash
            if (
                    receipt.receipt_inalterable_hash and 'receipt_inalterable_hash' in vals) or (
                    receipt.receipt_secure_sequence_number and 'receipt_secure_sequence_number' in vals):
                raise UserError(
                    _('You cannot overwrite the values ensuring the inalterability of the Receipt.'))
        res = super(AccountReceipt, self).write(vals)
        # write the hash and the secure_sequence_number when posting or invoicing a pos order
        if has_been_posted:
            for rec in self.filtered(
                    lambda r: r.receipt_restrict_mode_hash_table and not (
                            r.receipt_secure_sequence_number or r.receipt_inalterable_hash)).sorted(
                lambda r: (r.date, r.id)):
                new_number = rec.company_id.receipt_sequence_id.next_by_id()
                vals_hashing = {'receipt_secure_sequence_number': new_number,
                                'receipt_inalterable_hash': rec._get_new_hash(
                                    new_number)}
                res |= super(AccountReceipt, rec).write(vals_hashing)
        return res

    def button_open_payments(self):
        """Function redirect to created payment."""
        self.ensure_one()
        action = {
            'name': _("Payments"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'context': {'create': False, 'customer_payment': True},
        }
        if len(self.payment_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.payment_ids.id,
                'amount_total': self.total_pay_amount,
                'invoice_amount': self.invoice_amount,
                'currency_id': self.currency_id.id,
            })
        else:
            action.update({
                'view_mode': 'list,form',
                'domain': [('id', 'in', self.payment_ids.ids)],
            })
        return action

    def preview_receipt(self):
        """FUnction call to preview receipt."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.get_portal_url(),
        }

    def _compute_access_url(self):
        """Access url for portal"""
        super(AccountReceipt, self)._compute_access_url()
        for rec in self:
            rec.access_url = '/my/receipt/%s' % (rec.id)

    def _get_report_base_filename(self):
        """Report file name for portal."""
        self.ensure_one()
        return 'Receipt-%s' % (self.name)

    def unlink(self):
        """Function call to raise warning when unlink posted record."""
        for rec in self:
            if rec.state not in ('draft'):
                raise UserError(
                    _('You can not delete posted receipt.'))
        return super(AccountReceipt, self).unlink()

    def generic_payment_receipt(self, line):
        payment_obj = self.env['account.payment']
        icpsudo = request.env['ir.config_parameter'].sudo()
        pos_cash_payment_limit = icpsudo.get_param(
            "bizzup_pos_cash_limit.pos_cash_payment_limit"
        )
        if line.amount > int(pos_cash_payment_limit):
            if line.means_of_payment == '1' and line.amount > int(pos_cash_payment_limit):
                raise ValidationError(_(
                    'אינך יכול לשלם סכום כזה במזומן. נסה או סכום מתחת ל%s, או סכום הקטן מעשרה אחוז מסך העסקה, הנמוך מביניהם!'
                    % (pos_cash_payment_limit)))
            else:
                payment_vals = {
                    'date': self.date,
                    'amount': line.amount,
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'payment_reference': line.type,
                    'currency_id': line.currency_id.id,
                    'journal_id': line.journal_id.id,
                    'partner_id': self.partner_id.id,
                    'receipt_id': self.id,
                    'means_of_payment': line.means_of_payment or False,
                    'bank_number': line.bank_id.bank_code,
                    'branch_number': line.branch,
                    'account_number': line.credit_account_no,
                    'lyg_check_number': line.voucher_check_no,
                    'validity_date': line.validity_date
                }
                if self.company_id.withholding_tax_process and line.withholding_amount:
                    payment_vals['withholding_line_vals'] = {
                        'name': 'Withholding Payment',
                        'amount': line.withholding_amount,
                        'account_id': self.company_id.cust_withholding_tax_account_id.id,
                        'withholding_tax_process': True,

                    }
                    payment_vals.update({
                        'withholding_payment': True
                    })
                payments = payment_obj.create(payment_vals)
                if payments.name == "/" and self.company_id.withholding_tax_process and line.withholding_amount:
                    payments.name = payments.move_id.name
                payments.action_post()
                payments.name = payments.move_id.name
                payments.action_validate()
                line.write({"state": "post"})

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
        available_lines = self.env['account.move.line']
        for pay_line in self.receipt_line_ids.filtered(
                lambda inv: inv.type == 'invoice'):
            invoice_id = pay_line.invoice_id
            lines = self.env['account.move'].search(
                [('id', '=', invoice_id.id)]).line_ids
            for line in lines:
                if line.account_type not in ('asset_receivable', 'liability_payable'):
                    continue
                if line.company_currency_id.is_zero(line.amount_residual):
                    continue
                available_lines |= line
        lines = available_lines
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

    def action_post_receipt(self):
        """Function call to create payment and redirect to wizard."""
        remain_amount = self.remain_amount and eval(self.remain_amount) or {}
        if not self.receipt_line_ids:
            raise ValidationError(
                _("You can't confirm Receipt without Payment Lines."))
        for line in self.receipt_line_ids:
            if line.type == "generic" and line.state != "post":
                self.generic_payment_receipt(line)
        if all(
                [
                    line.type == "generic" and line.state == "post"
                    for line in self.receipt_line_ids
                ]
        ):
            self.write({'date': datetime.datetime.now()})
            self.write({"state": "post"})
            if self.name == _("New"):
                self.name = self.env["ir.sequence"].next_by_code(
                    "lyg.account.receipt"
                ) or _("New")
        if any([line.type == "invoice" for line in self.receipt_line_ids]):
            icpsudo = request.env['ir.config_parameter'].sudo()
            pos_cash_payment_limit = icpsudo.get_param(
                "bizzup_pos_cash_limit.pos_cash_payment_limit"
            )
            _logger.info(
                "\n\n -------IN ALL INVOICE CONDITION------- :\n%s",
                self.receipt_line_ids,
            )
            total_unpaid = self.receipt_line_ids.mapped(
                "invoice_id.amount_residual")
            total_line_invoice_ids = self.receipt_line_ids.mapped(
                "invoice_id")
            calculated_remain_amount = {
                inv.id: value
                for inv, value in zip(total_line_invoice_ids, total_unpaid)
            }
            _logger.info(
                "\n\n -------IN ALL INVOICE calculated_remain_amount------- :\n%s",
                calculated_remain_amount,
            )
            _logger.info(
                "\n\n -------IN ALL INVOICE remain_amount------- :\n%s",
                remain_amount.get(46, 0),
            )
            if line.invoice_amount > int(pos_cash_payment_limit):
                total_cash_amount = sum(
                    line.amount for line in self.receipt_line_ids if
                    line.means_of_payment == '1'
                )
                ten_percent = line.invoice_amount * 0.1
                if total_cash_amount > ten_percent or total_cash_amount > int(pos_cash_payment_limit):
                    raise ValidationError(_(
                        'אינך יכול לשלם סכום כזה במזומן. נסה או סכום מתחת ל%s, או סכום הקטן מעשרה אחוז מסך העסקה, הנמוך מביניהם!'
                    %(ten_percent if total_cash_amount > ten_percent else pos_cash_payment_limit)))
            for key, value in calculated_remain_amount.items():
                new_amount = "{:.2f}".format(remain_amount.get(key, 0))
            if all(float(new_amount) == value for key, value in calculated_remain_amount.items()):
                _logger.info(
                    "\n\n -------IN ALL INVOICE calculated_remain_amount------- :\n%s",
                    self.receipt_line_ids,
                )
                dict_len = eval(self.remain_amount)
                to_reconcile = []
                batches = self._get_payment_lines()
                if len(dict_len) > 1:
                    new_batches = []
                    for batch_result in batches:
                        for line_move in batch_result["lines"]:
                            new_batches.append(
                                {
                                    **batch_result,
                                    "lines": line_move,
                                }
                            )
                    batches = new_batches
                for batch_result in batches:
                    to_reconcile.append(batch_result["lines"])
                pay_dict = {}
                for line in self.receipt_line_ids.filtered(
                        lambda l: l.type == "invoice"
                ):
                    line.write({"state": "post"})
                    # append lines in it
                    # payment values for open and write-off
                    payment_vals = {
                        "date": datetime.datetime.now(),
                        "amount": line.amount,
                        "payment_type": "inbound",
                        "partner_type": "customer",
                        "memo": line.invoice_id.name,
                        "currency_id": self.currency_id.id,
                        "journal_id": line.journal_id.id,
                        # create payment for parent if availabe
                        "partner_id": self.partner_id.parent_id.id if self.partner_id.parent_id else self.partner_id.id,
                        "receipt_id": self.id,
                        "means_of_payment": line.means_of_payment or False,
                        "bank_number": line.bank_id.bank_code,
                        "branch_number": line.branch,
                        "account_number": line.credit_account_no,
                        "lyg_check_number": line.voucher_check_no,
                        "validity_date": line.validity_date,
                    }
                    if self.company_id.withholding_tax_process:
                        if line.withholding_amount:
                            # Append Write Off
                            payment_vals["withholding_line_vals"] = {
                                "name": "Withholding Payment",
                                "amount": line.withholding_amount,
                                "account_id": self.company_id.cust_withholding_tax_account_id.id,
                                "withholding_tax_process": True,
                            }
                            payment_vals.update({"withholding_payment": True})
                    payment_value_list = [payment_vals]
                    payments = self.env["account.payment"].create(
                        payment_value_list)
                    a = list(
                        filter(lambda l: l.move_id.name == payments.memo,
                               to_reconcile))
                    pay_dict[payments] = a[0] if a else 0
                for payment, line in pay_dict.items():
                    payment.action_post()
                    domain = [
                        ("account_type", "in",
                         ("asset_receivable", "liability_payable")),
                        ("reconciled", "=", False),
                    ]
                    payment_lines = payment.line_ids.filtered_domain(domain)
                    for account in payment_lines.account_id:
                        (payment_lines + line).filtered_domain(
                            [
                                ("account_id", "=", account.id),
                                ("reconciled", "=", False),
                            ]
                        ).reconcile()
                if all([line.state == "post" for line in
                        self.receipt_line_ids]):
                    if self.name == _("New"):
                        self.name = self.env["ir.sequence"].next_by_code(
                            "lyg.account.receipt"
                        ) or _("New")
                    self.write({'date': datetime.datetime.now()})
                    self.write(
                        {
                            "state": "post",
                        }
                    )
                self.receipt_line_ids.invoice_id.payment_state = 'paid'
            else:
                return {
                    "name": _("Register Payment"),
                    "res_model": "account.payment.wizard",
                    "view_mode": "form",
                    "context": {
                        "active_model": "account.payment.wizard",
                        "active_ids": self.id,
                        "default_remain_amount": self.remain_amount,
                    },
                    "target": "new",
                    "type": "ir.actions.act_window",
                }
        if self.env.user.lang == "he_IL":
            self.env.cr.commit()

            self.env.cr.execute("""
                UPDATE lyg_account_receipt
                SET name = jsonb_set(name, '{en_US}', to_jsonb(name->>'he_IL')::jsonb)
                WHERE id = %s
            """, (self.id,))


    def action_send_receipt(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        template_id = self.env.ref('lyg_receipt.lyg_mail_template_receipt').id
        ctx = {
            'default_model': 'lyg.account.receipt',
            'default_res_ids': self.ids,
            'default_use_template': bool(template_id),
            'default_template_id': template_id or False,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_light",
        }
        return {
            'name': _('Send Receipt'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def _cron_update_receipt_name(self):
        """
        Cron job to update old records' names in `lyg_account_receipt`
        where `state` is 'post', and both 'en_US' & 'he_IL' exist in `name`.
        If 'en_US' is 'New', it is replaced with 'he_IL' value.
        If 'he_IL' is 'New', it is replaced with 'en_US' value.
        """

        self.env.cr.execute("""
            SELECT id, name FROM lyg_account_receipt
            WHERE state = 'post' AND name ? 'en_US' AND name ? 'he_IL'
        """)
        records = self.env.cr.fetchall()

        for record_id, name_data in records:
            if isinstance(name_data, str):
                name_data = json.loads(name_data)

            en_us, he_il = name_data.get("en_US"), name_data.get("he_IL")

            if en_us and he_il and en_us != he_il:
                if en_us == "New":
                    name_data["en_US"] = he_il
                elif he_il == "New":
                    name_data["he_IL"] = en_us

                self.env.cr.execute("""
                    UPDATE lyg_account_receipt
                    SET name = %s
                    WHERE id = %s
                """, (json.dumps(name_data), record_id))


class AccountReceiptLine(models.Model):
    _name = "lyg.account.receipt.line"
    _description = "Receipt Lines"

    @api.model
    def default_get(self, fields):
        """Pass default value for amount field using context."""
        res = super(AccountReceiptLine, self).default_get(fields)
        context = self.env.context.copy()
        res.update({
            'amount': context.get('amount')
        })
        return res

    pay_receipt_id = fields.Many2one("lyg.account.receipt", "Receipt")
    journal_id = fields.Many2one('account.journal', "Journal", required=True)
    currency_id = fields.Many2one(related='pay_receipt_id.currency_id')
    amount = fields.Monetary("Amount", currency_field='currency_id')
    # added new field for withholding
    withholding_amount = fields.Monetary("Withholding Amount",
                                         currency_field='currency_id')
    withholding_tax_process = fields.Boolean(
        related="pay_receipt_id.company_id.withholding_tax_process")
    type = fields.Selection(
        [('invoice', 'Invoice'), ('generic', 'Generic')], "Type",
        default="generic")
    invoice_id = fields.Many2one('account.move', "Specific Invoice",
                                 copy=False,
                                 domain=[('move_type', '=', 'out_invoice'),
                                         ('amount_residual', '!=', 0),
                                         ('is_hmk', '=', False),
                                         ('state', '=', 'posted')])
    credit_account_no = fields.Char(string="Credit/Account Number")
    branch = fields.Char(string="Branch")
    bank_id = fields.Many2one('res.bank', string="Bank")
    voucher_check_no = fields.Char(string="Voucher/Check Number")
    validity_date = fields.Date(string="Redemption/Validity Date")
    invoice_amount = fields.Monetary("Unpaid Amount", copy=False,
                                     currency_field='currency_id',
                                     compute='_compute_remain_amount',
                                     store=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('post', 'Posted')], "State", default="draft")
    means_of_payment = fields.Selection(
        [('1', 'Cash'), ('2', 'Check'), ('3', 'Credit Card'),
         ('4', 'Bank Transfer'), ('5', 'Gift Card'), ('6', 'Return Note'),
         ('7', 'Promissory Note'), ('8', 'Standing Order'), ('9', 'Other')],
        default='1')

    @api.depends("invoice_id", "amount", "withholding_amount")
    def _compute_remain_amount(self):
        """Function call to compute default amount for lines."""
        for rec in self:
            invoice_dict = dict.fromkeys(list(
                set(rec.pay_receipt_id.receipt_line_ids.mapped(
                    'invoice_id.id'))), 0)
            for invoice in invoice_dict:
                current_invoice_lines = rec.pay_receipt_id.receipt_line_ids.filtered(
                    lambda rl: rl.invoice_id.id == invoice)
                line = current_invoice_lines[-1]
                line.invoice_amount = line.invoice_id.amount_residual
                if line.amount == 0:
                    line.amount = line.invoice_id.amount_residual - sum(
                        list(map(lambda y: y.amount + y.withholding_amount,
                                 filter(
                                     lambda x: list(
                                         current_invoice_lines).index(
                                         x) != len(current_invoice_lines) - 1,
                                     list(current_invoice_lines)))))
                invoice_dict[invoice] = float_round(
                    sum(current_invoice_lines.mapped(
                        'amount') + current_invoice_lines.mapped(
                        'withholding_amount')) or sum(
                        current_invoice_lines.mapped('invoice_amount')),
                    2)
            rec.pay_receipt_id.remain_amount = invoice_dict

    @api.onchange('pay_receipt_id.partner_id', 'type')
    def onchange_partner_id_inv(self):
        """Function call to change value of invoice based on partner selection."""
        if self.type == 'invoice':
            if not self.invoice_id:
                self.invoice_amount = 0.0
                self.amount = 0.0
            domain = []
            self.invoice_id = False
            remain_amount = self.pay_receipt_id.remain_amount and eval(
                self.pay_receipt_id.remain_amount) or {}
            if self.pay_receipt_id.partner_id:
                domain = [
                    ('partner_id', '=', self.pay_receipt_id.partner_id.id),
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted'),
                    ('payment_state', 'in', ['not_paid', 'partial'])]
            invoices = self.env['account.move'].search(domain)
            if remain_amount:
                invoices = invoices.filtered(
                    lambda inv: remain_amount.get(inv.id,
                                                  0) != inv.amount_residual)
            return {'domain': {'invoice_id': [('id', 'in', invoices.ids)]}}
        if self.type == 'generic':
            self.invoice_amount = 0.0
            self.amount = 0.0
            self.invoice_id = False
            domain = {'invoice_id': []}
            return {'domain': domain}

    @api.onchange('journal_id')
    def _onchange_receipt_line(self):
        if not self.pay_receipt_id.partner_id:
            raise ValidationError(_('You can not add lines without Partner.'))
