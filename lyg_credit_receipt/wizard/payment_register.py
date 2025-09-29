from odoo import models, fields, api, _
import datetime


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.wizard"

    def _get_payment_lines_credit_receipt(self):
        """Function get payment line."""
        active_id = self.env["lyg.account.receipt"].browse(
            self._context.get("active_id")
        )

        # active_id.ensure_one()
        available_lines = self.env["account.move.line"]
        for pay_line in active_id.receipt_line_ids.filtered(
            lambda inv: inv.type == "invoice"
        ):
            invoice_id = pay_line.invoice_id
            lines = (
                self.env["account.move"]
                .search([("id", "=", invoice_id.id)])
                .line_ids
            )

            for line in lines:
                available_lines |= line
        lines = available_lines
        batches = {}

        for line in lines:
            batch_key = active_id._get_line_multi_key(line)
            serialized_key = "-".join(str(v) for v in batch_key.values())
            batches.setdefault(
                serialized_key,
                {
                    "key_values": batch_key,
                    "lines": self.env["account.move.line"],
                },
            )
            batches[serialized_key]["lines"] += line
        return list(batches.values())

    def action_create_payment(self):
        """Function create payment with open and write-off option"""
        if "active_id" in self._context:
            active_id = self.env["lyg.account.receipt"].browse(
                self._context.get("active_id")
            )
            if active_id.is_credit_receipt:
                dict_len = eval(active_id.remain_amount)
                to_reconcile = []
                batches = self._get_payment_lines_credit_receipt()
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
                for line in active_id.receipt_line_ids.filtered(
                    lambda l: l.type == "invoice"
                ):
                    line.write({"state": "post"})
                    amount = line.amount - line.withholding_amount if self.company_id.withholding_tax_process and line.withholding_amount else line.amount
                    # append lines in it
                    # payment values for open and write-off
                    payment_vals = {
                        "date": datetime.datetime.now(),
                        "amount": amount,
                        "payment_type": "outbound",
                        "partner_type": "customer",
                        "memo": line.invoice_id.name,
                        "currency_id": self.currency_id.id,
                        "journal_id": line.journal_id.id,
                        "partner_id": active_id.partner_id.id,
                        "receipt_id": active_id.id,
                        "means_of_payment": line.means_of_payment or False,
                    }
                    # append write off vals in payment value

                    pay_line_write_off = (
                        self.invoice_receipt_line_ids.filtered(
                            lambda l: l.payment_difference_handling
                            == "reconcile"
                            and l.invoice_id == line.invoice_id
                        )
                    )
                    if pay_line_write_off:
                        last_payment_line = sorted(
                            active_id.receipt_line_ids.filtered(
                                lambda inv: inv.invoice_id
                                == pay_line_write_off.invoice_id
                            )
                        )
                        if (
                            last_payment_line
                            and line.id == last_payment_line[-1].id
                        ):
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
                    line.invoice_id.line_ids.remove_move_reconcile()
                    if line.type == "invoice" and line.invoice_id:
                        line.invoice_id.payment_state = "paid"
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
                    payment.name = payment.move_id.name

                    for account in payment_lines.account_id:
                        for pay_line in payment_lines:
                            credit_payment = self.env["account.payment"].search(
                                [("memo", "=", pay_line.ref)]
                            )
                        credit_payments = active_id.normal_receipt.payment_ids
                        (
                            payment_lines + credit_payment.move_id.line_ids
                        ).filtered_domain(
                            [
                                ("account_id", "=", account.id),
                                ("reconciled", "=", False),
                            ]
                        ).with_context(
                            credit_receipt=True
                        ).reconcile()

                        for pay in credit_payment:

                            if not pay.is_reconciled:

                                for (
                                    line
                                ) in active_id.normal_receipt.receipt_line_ids.filtered(
                                    lambda l: l.type == "invoice"
                                ):
                                    (
                                        line.invoice_id.line_ids +
                                        pay.move_id.line_ids
                                    ).filtered_domain(
                                        [
                                            ("account_id", "=", account.id),
                                            ("reconciled", "=", False),
                                        ]
                                    ).with_context(
                                        credit_receipt=True
                                    ).reconcile()
                if all(
                    [
                        line.state == "post"
                        for line in active_id.receipt_line_ids
                    ]
                ):

                    if active_id.name == _("New"):
                        active_id.name = active_id.env[
                            "ir.sequence"
                        ].next_by_code("lyg.account.receipt") or _("New")
                    active_id.write(
                        {
                            "state": "post",
                        }
                    )
            else:
                super(AccountPaymentRegister, self).action_create_payment()
