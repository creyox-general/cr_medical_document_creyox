from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
import datetime
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

INTEGRITY_HASH_RECEIPT_FIELDS = (
    "date",
    "invoice_id",
    "company_id",
    "partner_id",
    "receipt_user_id",
)
INTEGRITY_HASH_LINE_FIELDS = ("amount", "journal_id")


class AccountCreditReceipt(models.Model):
    _inherit = "lyg.account.receipt"

    is_credit_receipt = fields.Boolean(
        "Credit Receipt", default=False, copy=False
    )
    credit_receipt = fields.Many2one(
        "lyg.account.receipt", string="Credit Receipt"
    )
    normal_receipt = fields.Many2one(
        "lyg.account.receipt", string="Normal Receipt"
    )
    credit_receipt_count = fields.Integer(
        compute="compute_credit_receipt_count"
    )

    def compute_credit_receipt_count(self):
        for rec in self:
            if rec.credit_receipt:
                rec.credit_receipt_count = len(rec.credit_receipt)
            else:
                rec.credit_receipt_count = 0

    def generic_payment_receipt(self, line):
        payment_obj = self.env["account.payment"]
        amount = line.amount - line.withholding_amount if self.company_id.withholding_tax_process and line.withholding_amount else line.amount
        icpsudo = request.env['ir.config_parameter'].sudo()
        pos_cash_payment_limit = icpsudo.get_param(
            "bizzup_pos_cash_limit.pos_cash_payment_limit"
        )
        if not self.is_credit_receipt:
            if pos_cash_payment_limit:
                if line.means_of_payment == '1' and line.amount > int(
                    pos_cash_payment_limit
                    ):
                    raise ValidationError(
                        _(
                            'אינך יכול לשלם סכום כזה במזומן. נסה או סכום מתחת ל%s, או סכום הקטן מעשרה אחוז מסך העסקה, הנמוך מביניהם!'
                            % (pos_cash_payment_limit)
                        )
                    )
            payment_vals = {
                "date": datetime.datetime.now(),
                "amount": amount,
                "payment_type": "inbound",
                "partner_type": "customer",
                "payment_reference": line.type,
                "currency_id": line.currency_id.id,
                "journal_id": line.journal_id.id,
                # changes for create payment for parent
                "partner_id": self.partner_id.parent_id.id if self.partner_id.parent_id else self.partner_id.id,
                "receipt_id": self.id,
                "means_of_payment": line.means_of_payment or False,
                "bank_number": line.bank_id.bank_code,
                "branch_number": line.branch,
                "account_number": line.credit_account_no,
                "lyg_check_number": line.voucher_check_no,
                "validity_date": line.validity_date,
            }
            if (
                self.company_id.withholding_tax_process
                and line.withholding_amount
            ):
                payment_vals["withholding_line_vals"] = {
                    "name": "Withholding Payment",
                    "amount": line.withholding_amount,
                    "account_id": self.company_id.cust_withholding_tax_account_id.id,
                    "withholding_tax_process": True,
                }
                payment_vals.update({"withholding_payment": True})
            payments = payment_obj.create(payment_vals)
            payments.action_post()
            payments.name = payments.move_id.name
            payments.action_validate()
            line.write({"state": "post"})
        else:
            if self.normal_receipt.payment_ids:
                # Get all reconciled invoices from normal receipt payments
                reconciled_invoices = self.normal_receipt.payment_ids.mapped(
                    'reconciled_invoice_ids')
                invoices = [inv for sublist in reconciled_invoices for inv in
                            sublist]
                to_reconcile = []
                available_lines = self.env["account.move.line"]

                # Collect all reconcilable move lines from invoices
                for inv in invoices:
                    lines = inv.line_ids.filtered(
                        lambda l: l.account_id.reconcile)
                    available_lines |= lines

                # Organize move lines into batches
                batches = {}
                for move_line in available_lines:
                    batch_key = self._get_line_multi_key(move_line)
                    serialized_key = "-".join(
                        str(v) for v in batch_key.values())

                    if serialized_key not in batches:
                        batches[serialized_key] = {
                            "key_values": batch_key,
                            "lines": self.env["account.move.line"],
                        }
                    batches[serialized_key]["lines"] |= move_line

                # Flatten the batches for reconciliation
                new_batches = [{"key_values": b["key_values"], "lines": line}
                               for b in batches.values() for line in
                               b["lines"]]
                to_reconcile.extend(batch["lines"] for batch in new_batches)

                pay_dict = {}
                invoice_move_id = available_lines[
                    0] if available_lines else None

                # Process credit receipt payments
                if invoice_move_id:
                    payment_vals = {
                        "date": datetime.datetime.now(),
                        "amount": line.amount,
                        "payment_type": "outbound",
                        "partner_type": "customer",
                        "payment_reference": self.type,
                        "memo": invoice_move_id.move_id.name,
                        "currency_id": line.currency_id.id,
                        "journal_id": line.journal_id.id,
                        # changes for create payment for parent
                        "partner_id": self.partner_id.parent_id.id if self.partner_id.parent_id else self.partner_id.id,
                        "receipt_id": self.id,
                        "means_of_payment": line.means_of_payment or False,
                        "bank_number": line.bank_id.bank_code,
                        "branch_number": line.branch,
                        "account_number": line.credit_account_no,
                        "lyg_check_number": line.voucher_check_no,
                        "validity_date": line.validity_date,
                    }

                    # Add withholding tax if applicable
                    if self.company_id.withholding_tax_process and line.withholding_amount:
                        payment_vals.update({
                            "withholding_payment": True,
                            "withholding_line_vals": {
                                "name": "Withholding Payment",
                                "amount": line.withholding_amount,
                                "account_id": self.company_id.cust_withholding_tax_account_id.id,
                                "withholding_tax_process": True,
                            }
                        })

                    # Create payment record
                    payment_created = self.env["account.payment"].create(
                        payment_vals)
                    pay_dict[payment_created] = next(
                        filter(lambda
                                   l: l.move_id.name == payment_created.memo,
                               to_reconcile), None
                    )

                # Remove previous reconciliations for invoices
                if reconciled_invoices:
                    reconciled_invoices.line_ids.remove_move_reconcile()

                # Post and reconcile payments
                for payment, line in pay_dict.items():
                    if payment.amount == 0:
                        payment.state = 'draft'
                    else:
                        payment.action_post()

                    # Get reconcilable move lines
                    payment_lines = payment.move_id.line_ids.filtered(
                        lambda l: l.account_type in ("asset_receivable",
                                                     "liability_payable") and not l.reconciled
                    )
                    # Reconcile payment lines with existing ones
                    for account in payment_lines.mapped("account_id"):
                        lines_to_reconcile = (
                                payment_lines +
                                self.normal_receipt.payment_ids.move_id.mapped(
                                    "line_ids")
                        ).filtered(lambda
                                       l: l.account_id == account and not l.reconciled)
                        lines_to_reconcile.with_context(
                            credit_receipt=True).reconcile()
                        # Reconcile remaining normal receipt payments
                        for pay in self.normal_receipt.payment_ids:
                            if not pay.is_reconciled:
                                for line in self.normal_receipt.receipt_line_ids.filtered(
                                        lambda l: l.type == "generic"):
                                    reconciliation_lines = (
                                            reconciled_invoices.line_ids + pay.move_id.line_ids
                                    ).filtered(lambda
                                                   l: l.account_id == account and not l.reconciled)
                                    reconciliation_lines.with_context(
                                        credit_receipt=True).reconcile()
                # Set receipt name sequence if still "New"
                if self.name == _("New"):
                    self.name = self.env["ir.sequence"].next_by_code(
                        "lyg.account.receipt") or _("New")

                # Mark receipt as posted
                self.write({"state": "post"})

                # Fetch payments related to this receipt
                payments = self.env["account.payment"].search(
                    [("receipt_id.name", "=", self.name)], order="id DESC"
                )
                # Unlink zero-amount payments related to specific credit lines
                for pay in payments:
                    matching_cred_line = self.receipt_line_ids.filtered(
                        lambda l: l.amount == pay.amount)
                    if pay.amount == 0.0 and matching_cred_line and not pay.is_reconciled:
                        pay.unlink()

    def action_post_credit_receipt(self):
        credit_receipt_lines = []
        for rec in self.receipt_line_ids:
            credit_receipt_lines.append(
                (
                    (
                        0,
                        0,
                        {
                            "journal_id": rec.journal_id.id,
                            "currency_id": rec.currency_id.id,
                            "amount": rec.amount,
                            "withholding_amount": rec.withholding_amount,
                            "withholding_tax_process": rec.withholding_tax_process,
                            "type": rec.type,
                            "invoice_id": rec.invoice_id.id,
                            "credit_account_no": rec.credit_account_no,
                            "branch": rec.branch,
                            "bank_id": rec.bank_id.id,
                            "voucher_check_no": rec.voucher_check_no,
                            "validity_date": rec.validity_date,
                            "invoice_amount": rec.invoice_amount,
                            "means_of_payment": rec.means_of_payment,
                        },
                    )
                )
            )

        credit_receipt_id = self.create(
            {
                "name": str(
                    self.env["ir.sequence"].next_by_code(
                        "lyg.account.credit.receipt"
                    )
                    or _("New")
                ),
                "subject": "Credit Receipt for receipt " + str(self.name),
                'date': datetime.datetime.now(),
                "partner_id": self.partner_id.id,
                "type": self.type,
                # 'invoice_id': self.invoice_id.id,
                "currency_id": self.currency_id.id,
                "currency_code": self.currency_code,
                "receipt_line_ids": credit_receipt_lines,
                "state": "draft",
                "company_id": self.company_id.id,
                "total_pay_amount": self.total_pay_amount,
                "total_ils": self.total_ils,
                "invoice_amount": self.invoice_amount,
                "receipt_user_id": self.receipt_user_id.id,
                "remain_amount": self.remain_amount,
                "is_credit_receipt": True,
                "normal_receipt": self.id,
            }
        )
        for rec in credit_receipt_id.filtered(
            lambda r: r.receipt_restrict_mode_hash_table
            and not (
                r.receipt_secure_sequence_number or r.receipt_inalterable_hash
            )
        ).sorted(lambda r: (r.date, r.id)):
            new_number = rec.company_id.receipt_sequence_id.next_by_id()
            vals_hashing = {
                "receipt_secure_sequence_number": new_number,
                "receipt_inalterable_hash": rec._get_new_hash(new_number),
            }
            credit_receipt_id.write(vals_hashing)
        self.update(
            {
                "credit_receipt": credit_receipt_id.id,
            }
        )
        return {
            "name": "Credit Receipts",
            "res_model": "lyg.account.receipt",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_id": credit_receipt_id.id,
            "target": "current",
        }

    def action_post_receipt(self):
        """Function call to create payment and redirect to wizard."""
        remain_amount = self.remain_amount and eval(self.remain_amount) or {}
        if not self.receipt_line_ids:
            raise ValidationError(
                _("You can't confirm Receipt without Payment Lines.")
            )
        for line in self.receipt_line_ids:
            if line.type == "generic" and line.state != "post":
                self.generic_payment_receipt(line)
                if self.name == _("New"):
                    self.name = self.env["ir.sequence"].next_by_code(
                        "lyg.account.receipt"
                    ) or _("New")
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
                "invoice_id.amount_residual"
            )
            total_line_invoice_ids = self.receipt_line_ids.mapped("invoice_id")
            calculated_remain_amount = {
                inv.id: value
                for inv, value in zip(total_line_invoice_ids, total_unpaid)
            }
            _logger.info(
                "\n\n -------IN ALL INVOICE calculated_remain_amount------- :\n%s",
                calculated_remain_amount,
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
                        % (ten_percent if total_cash_amount > ten_percent else pos_cash_payment_limit)))
            if all(
                remain_amount.get(key, 0) == value
                for key, value in calculated_remain_amount.items()
            ):
                _logger.info(
                    "\n\n -------IN ALL INVOICE calculated_remain_amount------- :\n%s",
                    self.receipt_line_ids,
                )
                # dict_len = eval(self.remain_amount)
                _logger.info(
                    "\n\n -------remain_amount------- :\n%s",
                    self.remain_amount,
                )
                _logger.info(
                    "\n\n -------remain_amount_type------- :\n%s",
                    type(self.remain_amount),
                )
                dict_len = eval(self.remain_amount)
                _logger.info("\n\n -------dict_len------- :\n%s", dict_len)
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
                        "payment_type": (
                            "inbound"
                            if not self.is_credit_receipt
                            else "outbound"
                        ),
                        "partner_type": "customer",
                        "memo": line.invoice_id.name,
                        "currency_id": self.currency_id.id,
                        "journal_id": line.journal_id.id,
                        # changes for create payment for parent
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
                        payment_value_list
                    )
                    pay_dict[payments] = list(
                        filter(
                            lambda l: l.move_id.name == payments.memo,
                            to_reconcile,
                        )
                    )[0]
                for payment, line in pay_dict.items():
                    payment.action_post()
                    domain = [
                        (
                            "account_type",
                            "in",
                            ("asset_receivable", "liability_payable"),
                        ),
                        ("reconciled", "=", False),
                    ]
                    payment_lines = payment.move_id.line_ids.filtered_domain(
                        domain)
                    for account in payment_lines.account_id:
                        (payment_lines + line).filtered_domain(
                            [
                                ("account_id", "=", account.id),
                                ("reconciled", "=", False),
                            ]
                        ).reconcile()
                if all(
                    [line.state == "post" for line in self.receipt_line_ids]
                ):
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
    def button_credit_receipts(self):
        """Function redirect to created credit receipt."""
        self.ensure_one()
        action = {
            "name": _("Credit Receipt"),
            "type": "ir.actions.act_window",
            "res_model": "lyg.account.receipt",
            "view_mode": "form",
            "res_id": self.credit_receipt.id,
        }
        return action
