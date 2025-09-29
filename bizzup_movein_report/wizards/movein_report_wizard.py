# -*- coding: utf-8 -*-
import base64
import logging
import re
from datetime import datetime

from lxml import etree
from odoo import models, fields, _
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class MoveinReportWizard(models.TransientModel):
    _name = "movein.report.wizard"
    _description = "Movein Report"

    start_date = fields.Date(
        "Start Date", default=datetime.now().date().replace(month=1, day=1)
    )
    end_date = fields.Date(
        "End Date", default=datetime.now().date().replace(month=12, day=31)
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    state = fields.Selection([("choose", "choose"), ("get", "get")], default="choose")
    movein_filename = fields.Char()
    movein_data = fields.Binary("Movein Report", readonly=True, attachment=False)

    movein_prm_filename = fields.Char()
    movein_prm_data = fields.Binary(
        "Movein PRM Report", readonly=True, attachment=False
    )

    def _get_self_indicators(self):
        icpsudo = request.env["ir.config_parameter"].sudo()
        indicator_rivhit = icpsudo.get_param("bizzup_movein_report.is_for_rivhit")
        indicator_hrp = icpsudo.get_param("bizzup_movein_report.is_for_hrp")
        return indicator_rivhit, indicator_hrp

    # Format fields based on required display settings in MOVEIN
    @staticmethod
    def format_string(value, length, padding_char=' ', align='right'):
        value = str(value or '')
        if len(value) < length:
            if align == 'right':
                return value.rjust(length, padding_char)
            else:
                return value.ljust(length, padding_char)
        else:
            return value[:length]

    def check_unique_debit_credit(self, journal_entry):
        """
        Checks if all lines in the current account moves have the same account.
        :return: True if all lines in all account moves have the same account, False otherwise.
        """
        for move in journal_entry:
            # Get all account IDs from the lines
            account_ids = move.line_ids.mapped("account_id.code")

            # Check if all accounts are the same
            if len(set(account_ids)) > 1:
                return True  # Not all lines have the same account
        return False  # All lines in all account moves have the same account

    def get_document_vals(self):
        start_date = self.start_date
        end_date = self.end_date
        _is_for_rivhit, _is_for_hrp = self._get_self_indicators()
        if start_date > end_date:
            raise ValidationError(
                _(
                    "Please add valid dates. Start date can not be greater than end date."
                )
            )
        _logger.info(
            "\n\n -------user company name------- :\n%s", self.env.company.name
        )
        journal_entry = self.env["account.move"].search(
            [
                ("state", "=", "posted"),
                ("date", ">=", start_date),
                ("date", "<=", end_date),
                ("amount_total", ">", 0),
                ("company_id", "=", self.env.company.id),
            ]
        )
        docs = []
        journal_data = {}
        if not journal_entry:
            raise ValidationError(_("No Journal Entries found in this period."))
        for journal in journal_entry:
            repeated_lines = self.check_unique_debit_credit(journal)
            if repeated_lines:

                name = (
                    re.sub(r"^\w+\s*", "", journal.name)
                    .replace("/20", "")
                    .replace("/", "")
                    .replace("-D", "")
                    .replace("-1", "")
                )

                # Getting the debit account codes and debit amounts

                # Debit Account Codes and VAT Account Codes
                journal_tax_ids = journal.invoice_line_ids.filtered(
                    lambda line: line.tax_ids
                                 and (tax.amount == 0 for tax in line.tax_ids)
                )
                journal_debit_accounts = journal.line_ids.filtered(
                    lambda line: line.debit != 0 or line.credit != 0
                )
                if journal_debit_accounts:
                    journal_debit_accounts = journal.line_ids.filtered(
                        lambda line: line.debit != 0
                    )
                    journal_debit_vat_accounts = journal_debit_accounts.filtered(
                        lambda line: line.name and "%" in line.name
                    )
                    journal_debit_account_codes = journal_debit_accounts.mapped(
                        "account_id.code"
                    )
                    journal_debit_vat_account_codes = journal_debit_vat_accounts.mapped(
                        "account_id.code"
                    )
                    journal_debit_external_software_code = (
                        journal_debit_accounts.mapped(
                            "account_id.external_software_code"
                        )[0]
                        if len(
                            journal_debit_accounts.mapped(
                                "account_id.external_software_code"
                            )
                        )
                           > 0
                        else None
                    )

                    debit_receivable_account_type = (
                        journal_debit_accounts.mapped("account_id.account_type")[1]
                        if len(journal_debit_accounts.mapped("account_id.account_type")) > 1
                        else journal_debit_accounts.mapped("account_id.account_type")[0]
                    )

                    debit_non_receivable_account_type = (
                        journal_debit_accounts.mapped("account_id.account_type")[0]
                        if len(journal_debit_accounts.mapped("account_id.account_type")) > 0
                        else ""
                    )

                    debit_non_receivable_account_code = (
                        journal_debit_accounts.mapped(
                            "account_id.external_software_code"
                        )[0]
                        if debit_non_receivable_account_type != "asset_receivable"
                           and journal_debit_accounts.mapped(
                            "account_id.external_software_code"
                        )[0] > 0
                        else ""
                    )

                    journal_debit_vat_external_software_code = (
                        journal_debit_vat_accounts.mapped(
                            "account_id.external_software_code"
                        )[0]
                        if len(
                            journal_debit_vat_accounts.mapped(
                                "account_id.external_software_code"
                            )
                        ) > 0
                        else None
                    )

                    debit_account_code_helper = list(journal_debit_account_codes).copy()
                    if "100100" in debit_account_code_helper:
                        debit_account_code_helper.remove("100100")
                    if "100110" in debit_account_code_helper:
                        debit_account_code_helper.remove("100110")

                    debit_account_code_1 = str(
                        journal_debit_account_codes[1]
                        if len(journal_debit_account_codes) == 2
                           and journal.move_type == "out_invoice"
                           and debit_receivable_account_type == "asset_receivable"
                        else journal_debit_account_codes[-1]
                        if len(journal_debit_account_codes) == 3
                           and journal.is_pos_entry
                           and journal.move_type == "entry"
                        # As default, remove rounding accounts
                        else debit_account_code_helper[0]
                        if len(debit_account_code_helper) > 0
                        else ""
                    )

                    debit_account_code_2 = str(
                        journal_debit_vat_external_software_code
                        if journal_debit_vat_external_software_code
                        else journal_debit_vat_account_codes[0]
                        if len(journal_debit_vat_account_codes) > 0
                           and journal_debit_vat_account_codes
                        else debit_non_receivable_account_code
                        if debit_non_receivable_account_type
                           and len(journal_debit_account_codes) > 1
                        else journal_debit_account_codes[1]
                        if len(
                            journal_debit_accounts.mapped("debit")
                            and journal_debit_account_codes) == 2
                            and not journal.is_pos_entry
                        else ""
                    )

                    external_code_debit = (
                        journal_debit_accounts.mapped(
                            "account_id.external_software_code"
                        )[1]
                        if len(
                            journal_debit_accounts.mapped(
                                "account_id.external_software_code")) == 2
                        else ""
                    )

                    debit_account_code_3 = str(
                        journal_debit_account_codes[0]
                        if len(
                            journal_debit_accounts.mapped("debit")
                            and journal_debit_account_codes) == 2
                           and debit_non_receivable_account_type != "asset_receivable"
                           and journal.move_type == "out_invoice"
                        else external_code_debit
                        if external_code_debit != 0
                        else journal_debit_account_codes[1]
                        if len(
                            journal_debit_accounts.mapped("debit")
                            and journal_debit_account_codes) == 2
                        else ""
                    )

                    # Withholding debit account codes
                    withholding_debit_account_code = (
                        journal_debit_account_codes[1]
                        if journal.move_type == "entry"
                           and journal.is_withholding
                           and len(journal_debit_account_codes) > 1
                        else ""
                    )

                    # Debit Amounts and VAT Amounts
                    journal_debit_amount = journal_debit_accounts.mapped("debit")
                    journal_debit_vat_amount = journal_debit_vat_accounts.mapped(
                        "debit"
                    )

                    debit_non_receivable_amount = (
                        journal_debit_accounts.mapped("debit")[0]
                        if debit_non_receivable_account_type != "asset_receivable"
                           and len(journal_debit_accounts.mapped("debit")) == 1
                        else ""
                    )

                    debit_amount_1 = str(
                        "{:.2f}".format(journal_debit_amount[-1])
                        if len(journal_debit_amount) > 2 and journal_debit_vat_amount
                        else "{:.2f}".format(journal_debit_amount[1])
                        if len(journal_debit_account_codes) > 1 > len(journal_debit_amount)
                        else "{:.2f}".format(sum(journal_debit_amount))
                        if len(journal_debit_amount) <= 1
                        else "{:.2f}".format(sum(journal_debit_amount))
                        if len(journal_debit_account_codes) <= 1
                        else "{:.2f}".format(journal_debit_amount[0])
                        if len(journal_debit_amount) == 2
                           and debit_receivable_account_type == "asset_receivable"
                           and journal.is_pos_entry
                           and journal.move_type == "entry"
                        else "{:.2f}".format(journal_debit_amount[1])
                        if len(journal_debit_amount) == 2
                           and debit_receivable_account_type == "asset_receivable"
                        else "{:.2f}".format(journal_debit_amount[1])
                        if journal.move_type == "in_refund"
                           and len(journal_debit_amount) == 2
                           and journal.amount_tax == 0
                           and debit_non_receivable_account_type != "asset_receivable"
                        else "{:.2f}".format(journal_debit_amount[0])
                        if journal.move_type
                           in ("entry", "in_refund", "in_invoice", "out_invoice")
                           and len(journal_debit_amount) == 2
                           and journal.amount_tax == 0
                           and debit_non_receivable_account_type != "asset_receivable"
                        else "{:.2f}".format(journal_debit_amount[0])
                        if journal.move_type
                           in ("entry", "in_refund", "in_invoice", "out_invoice")
                           and len(journal_debit_amount) == 2
                           and journal.amount_tax == 0
                           and debit_non_receivable_account_type == "asset_receivable"
                        else "{:.2f}".format(journal_debit_amount[1])
                        if journal.move_type
                           in ("entry", "in_refund", "in_invoice", "out_invoice")
                           and len(journal_debit_amount) == 2
                           and journal.amount_tax == 0
                        else "{:.2f}".format(journal_debit_amount[0])
                        if journal.move_type
                           in ("entry", "in_refund", "in_invoice", "out_invoice")
                           and len(journal_debit_amount) == 2
                        else "{:.2f}".format(journal_debit_amount[0])
                        if len(journal_debit_amount) > 2
                           and len(journal_debit_account_codes) >= 2
                           and journal.move_type != "out_invoice"
                        else "{:.2f}".format(journal.amount_total)
                        if len(journal_debit_amount) > 2
                           and journal.move_type == "out_invoice"
                           and journal.amount_tax == 0
                        else "{:.2f}".format(journal.amount_total)
                        if len(journal_debit_amount) > 2
                           and journal.move_type in ("out_invoice", "out_refund")
                           and not journal_debit_vat_amount
                           and _is_for_hrp
                        else "{:.2f}".format(journal.amount_total)
                        if len(journal_debit_amount) == 3
                           and journal.move_type == "out_invoice"
                           and not journal_debit_vat_amount
                        else "{:.2f}".format(sum(journal_debit_amount[:-1]))
                    ).replace(".", "")

                    debit_amount_2 = str(
                        "{:.2f}".format(journal_debit_vat_amount[0])
                        if len(journal_debit_vat_amount) > 0
                        else "{:.2f}".format(debit_non_receivable_amount)
                        if debit_account_code_2 and debit_non_receivable_amount
                        else "{:.2f}".format(sum(journal_debit_amount[:-1]))
                        if len(journal_debit_amount) == 3
                           and journal.move_type == "out_invoice"
                           and not journal_debit_vat_amount
                        else journal_debit_accounts.mapped("debit")[-1]
                        if len(journal_debit_accounts.mapped("debit")) > 2
                           and journal.move_type == "out_invoice"
                        else "{:.2f}".format(journal_debit_amount[0])
                        if len(journal_debit_amount and journal_debit_account_codes)
                           == 2
                           and debit_non_receivable_account_type != "asset_receivable"
                           and journal.move_type == "out_invoice"
                        else "{:.2f}".format(sum(journal_debit_amount[1:]))
                        if len(journal_debit_amount) > 2
                           and len(journal_debit_account_codes) >= 2
                        else "{:.2f}".format(journal_debit_amount[1])
                        if len(journal_debit_amount) == 2
                           and len(journal_debit_account_codes) == 2
                           and journal.move_type == "out_refund"
                           and "-" + str(journal.amount_total)
                           == str(journal_debit_amount[0])
                        else "{:.2f}".format(journal_debit_amount[0])
                        if len(journal_debit_amount) == 2
                           and len(journal_debit_account_codes) == 2
                           and journal.move_type == "out_refund"
                        else "{:.2f}".format(journal_debit_amount[1])
                        if len(journal_debit_amount and journal_debit_account_codes)
                           == 2
                        else ""
                    ).replace(".", "")

                    # External Software Code and Receipt Debit for Debit Accounts
                    receipt_debit_journal_entry = str(
                        journal.partner_id.receipt_debit
                        if journal.origin_payment_id.payment_type == "outbound"
                           and journal.partner_id.receipt_debit
                        else ""
                    )

                    receipt_debit_customer_invoice = str(
                        journal.partner_id.receipt_debit
                        if journal.move_type == "out_invoice"
                           and journal.partner_id.receipt_debit
                        else journal_debit_accounts.mapped(
                            "account_id.external_software_code"
                        )[1]
                        if len(
                            journal_debit_accounts.mapped(
                                "account_id.external_software_code"
                            )
                        )
                           > 1
                           and debit_receivable_account_type == "asset_receivable"
                           and journal_debit_accounts.mapped(
                            "account_id.external_software_code"
                        )[1]
                           != 0
                        else ""
                    )

                    receipt_debit_vendor_credit_note = str(
                        journal.partner_id.receipt_debit
                        if journal.move_type == "in_refund"
                           and journal.partner_id.receipt_debit
                           and journal.partner_id.receipt_debit != 0
                        else journal_debit_accounts.mapped(
                            "account_id.external_software_code"
                        )[1]
                        if len(
                            journal_debit_accounts.mapped(
                                "account_id.external_software_code"
                            )
                        )
                           > 1
                           and journal_debit_accounts.mapped(
                            "account_id.external_software_code"
                        )[1]
                           != 0
                           and debit_receivable_account_type == "liability_payable"
                        else ""
                    )

                    # Withholding debit amount
                    withholding_debit_amount = (
                        "{:.2f}".format(journal_debit_amount[1])
                        if journal.move_type == "entry"
                           and journal.is_withholding
                           and len(journal_debit_account_codes) > 1
                           and len(journal_debit_amount) > 1
                        else ""
                    ).replace(".", "")

                    withholding_debit_amount_1 = (
                        "{:.2f}".format(sum(journal_debit_amount))
                        if journal.origin_payment_id.receipt_id.is_credit_receipt
                           and journal.move_type == "entry"
                           and journal.is_withholding
                           and len(journal_debit_account_codes) > 1
                           and len(journal_debit_amount) > 1
                        else "{:.2f}".format(journal_debit_amount[0])
                        if journal.move_type == "entry" and journal.is_withholding
                        else ""
                    ).replace(".", "")

                    # Getting the credit account codes and credit amount

                    # Credit Account codes and VAT Account Codes
                    journal_credit_accounts = journal.line_ids.filtered(
                        lambda line: line.credit > 0 or line.credit < 0
                    )
                    journal_credit_vat_accounts = journal_credit_accounts.filtered(
                        lambda line: line.name and "%" in line.name
                    )
                    journal_credit_account_codes = journal_credit_accounts.mapped(
                        "account_id.code"
                    )
                    journal_credit_vat_account_codes = (
                        journal_credit_vat_accounts.mapped("account_id.code")
                    )
                    journal_credit_external_software_code = (
                        journal_credit_accounts.mapped(
                            "account_id.external_software_code"
                        )[1]
                        if len(
                            journal_credit_accounts.mapped(
                                "account_id.external_software_code"
                            )
                        )
                           == 3
                           and journal.amount_tax == 0
                           and journal_credit_accounts.mapped(
                            "account_id.external_software_code"
                        )[-1]
                           == 0
                        else journal_credit_accounts.mapped(
                            "account_id.external_software_code"
                        )[-1]
                        if len(
                            journal_credit_accounts.mapped(
                                "account_id.external_software_code"
                            )
                        )
                           == 3
                           and journal.amount_tax == 0
                        else journal_credit_accounts.mapped(
                            "account_id.external_software_code"
                        )[0]
                        if len(
                            journal_credit_accounts.mapped(
                                "account_id.external_software_code"
                            )
                        )
                           > 0
                        else None
                    )

                    credit_payable_account_type = (
                        journal_credit_accounts.mapped("account_id.account_type")[1]
                        if len(
                            journal_credit_accounts.mapped("account_id.account_type")
                        )
                           > 1
                        else journal_credit_accounts.mapped("account_id.account_type")[
                            0
                        ]
                    )

                    credit_non_payable_account_type = (
                        journal_credit_accounts.mapped("account_id.account_type")[0]
                        if len(
                            journal_credit_accounts.mapped("account_id.account_type")
                        )
                           > 0
                        else ""
                    )

                    credit_non_payable_account_code = (
                        journal_credit_accounts.mapped(
                            "account_id.external_software_code"
                        )[0]
                        if credit_non_payable_account_type != "liability_payable"
                           and journal_credit_accounts.mapped(
                            "account_id.external_software_code"
                        )[0]
                           > 0
                        else ""
                    )

                    journal_credit_vat_external_software_code = (
                        journal_credit_vat_accounts.mapped(
                            "account_id.external_software_code"
                        )[0]
                        if len(
                            journal_credit_vat_accounts.mapped(
                                "account_id.external_software_code"
                            )
                        )
                           > 0
                        else None
                    )

                    credit_account_code_1 = str(
                        journal_credit_account_codes[0]
                        if len(journal_credit_account_codes) >= 2
                           and journal.is_pos_entry
                           and journal.move_type == "entry"
                           and journal_credit_account_codes[-1] == debit_account_code_1
                        else journal_credit_account_codes[-1]
                        if len(journal_credit_account_codes) >= 2
                           and journal.is_pos_entry
                           and journal.move_type == "entry"
                        else journal_credit_account_codes[0]
                        if len(journal_credit_account_codes) > 0
                        else ""
                    )

                    external_code = (
                        credit_non_payable_account_code
                        if credit_non_payable_account_code
                           and len(
                            journal_credit_accounts.mapped(
                                "account_id.external_software_code"
                            )
                        )
                           == 2
                        else journal_credit_accounts.mapped(
                            "account_id.external_software_code"
                        )[1]
                        if journal.move_type
                           in ("in_invoice", "out_invoice", "out_refund", "in_refund")
                           and len(journal_credit_account_codes) == 2
                           and credit_payable_account_type != "liability_payable"
                           and len(
                            journal_credit_accounts.mapped(
                                "account_id.external_software_code"
                            )
                        )
                           == 2
                        else ""
                    )

                    credit_account_code_2 = str(
                        journal_credit_vat_external_software_code
                        if journal_credit_vat_external_software_code
                        else journal_credit_vat_account_codes[0]
                        if len(journal_credit_account_codes) == 1
                           and journal_credit_vat_account_codes
                        else credit_non_payable_account_code
                        if credit_non_payable_account_code
                           and len(journal_credit_account_codes) > 1
                           and credit_account_code_1 != journal_credit_account_codes[0]
                        else external_code
                        if external_code
                        else journal_credit_account_codes[1]
                        if journal.move_type
                           in ("in_invoice", "out_invoice", "entry", "in_refund")
                           and len(journal_credit_account_codes) == 2
                           and credit_payable_account_type != "liability_payable"
                        else journal_credit_account_codes[0]
                        if journal.is_pos_entry
                           and journal.move_type == "entry"
                           and len(journal_credit_account_codes) > 2
                        else ""
                    )

                    credit_extra_code = (
                        journal_credit_account_codes[1]
                        if len(
                            journal_credit_accounts.mapped("credit")
                            and journal_credit_account_codes
                        )
                           == 2
                        else ""
                    )

                    credit_account_code_3 = str(
                        journal_credit_account_codes[0]
                        if credit_account_code_1 == credit_extra_code
                        else journal_credit_vat_account_codes[0]
                        if len(journal_credit_account_codes) == 2
                           and len(journal_credit_vat_account_codes) > 0
                           and journal.move_type == "out_refund"
                           and _is_for_hrp
                        else credit_account_code_1
                        if len(
                            journal_credit_accounts.mapped("credit")
                            and journal_credit_account_codes
                        )
                           == 2
                        else ""
                    )

                    # Withholding credit account codes
                    withholding_credit_account_code = (
                        journal_credit_account_codes[1]
                        if journal.move_type == "entry"
                           and journal.is_withholding
                           and len(journal_credit_account_codes) > 1
                        else ""
                    )

                    # Credit Amounts and VAT Amounts
                    journal_credit_amount = journal_credit_accounts.mapped("credit")
                    journal_credit_vat_amount = journal_credit_vat_accounts.mapped(
                        "credit"
                    )

                    credit_non_payable_amount = (
                        journal_credit_accounts.mapped("credit")[0]
                        if debit_non_receivable_account_type != "liability_payable"
                           and len(journal_debit_accounts.mapped("credit")) > 0
                        else ""
                    )

                    credit_amount_1 = str(
                        "{:.2f}".format(sum(journal_credit_amount[:-1]))
                        if len(journal_credit_amount) > 2
                           and journal_credit_vat_amount
                           and journal.amount_tax != 0
                        else "{:.2f}".format(journal_credit_amount[1])
                        if len(journal_credit_account_codes) > 1
                           and len(journal_credit_amount) < 2
                        else "{:.2f}".format(journal_credit_amount[1])
                        if len(journal_credit_amount) == 2
                           and credit_payable_account_type == "liability_payable"
                        else "{:.2f}".format(journal_credit_amount[1])
                        if len(journal_credit_amount) > 2
                           and credit_payable_account_type == "liability_payable"
                           and journal.move_type == "in_invoice"
                           and journal.currency_id.name == "GBP"
                        else "{:.2f}".format(journal_credit_amount[-1])
                        if len(journal_credit_amount) > 2
                           and credit_payable_account_type == "liability_payable"
                        else "{:.2f}".format(journal_credit_amount[1])
                        if len(journal_credit_amount) > 2
                           and len(journal_credit_account_codes) == 2
                           and credit_payable_account_type == "liability_payable"
                        else "{:.2f}".format(journal.amount_total)
                        if len(journal_credit_amount) >= 2
                           and journal.move_type == "out_invoice"
                           and journal.amount_tax == 0
                        else "{:.2f}".format(sum(journal_credit_amount))
                        if len(journal_credit_account_codes) == 1
                           and journal.move_type != "out_refund"
                        else "{:.2f}".format(journal.amount_total)
                        if len(journal_credit_amount) > 2
                           and journal.move_type == "in_invoice"
                           and _is_for_hrp
                        else "{:.2f}".format(journal_credit_amount[0])
                        if len(journal_credit_amount) == 3
                           and len(journal_credit_account_codes) == 2
                           and journal.move_type == "in_invoice"
                        else "{:.2f}".format(journal_credit_amount[-1])
                        if len(journal_credit_amount) > 2
                           and journal.move_type == "in_invoice"
                        else "-" + str("{:.2f}".format(journal_credit_amount[0]))
                        if journal.move_type == "out_refund"
                           and len(journal_credit_amount) == 1
                           and len(journal_credit_account_codes) == 1
                        else "-" + str("{:.2f}".format(journal.amount_untaxed))
                        if journal.move_type == "out_refund"
                        else "{:.2f}".format(journal_credit_amount[-1])
                        if len(journal_credit_amount) == 2
                           and journal.move_type == "out_refund"
                           and credit_payable_account_type != "liability_payable"
                        else "{:.2f}".format(sum(journal_credit_amount))
                        if len(journal_credit_amount) > 2
                           and journal.move_type == "out_invoice"
                           and not debit_amount_2
                        else "{:.2f}".format(journal_credit_amount[-1])
                        if len(journal_credit_amount) == 4
                           and len(journal_credit_account_codes) >= 2
                           and journal.move_type == "in_refund"
                        else "{:.2f}".format(
                            journal_credit_amount[1] + journal_credit_amount[2]
                        )
                        if len(journal_credit_amount) > 3
                           and len(journal_credit_account_codes) > 3
                           and journal.is_pos_entry
                           and journal.move_type == "entry"
                        else "{:.2f}".format(journal_credit_amount[1])
                        if len(journal_credit_amount) == 2
                           and len(journal_credit_account_codes) == 2
                           and journal.is_pos_entry
                           and journal.move_type == "entry"
                        else "{:.2f}".format(sum(journal_credit_amount[1:]))
                        if len(journal_credit_amount) == 3
                           and len(journal_credit_account_codes) == 3
                           and journal.is_pos_entry
                           and journal.move_type == "entry"
                        else "{:.2f}".format(journal_credit_amount[0])
                        if len(journal_credit_amount) >= 2
                           and len(journal_credit_account_codes) >= 2
                        else "{:.2f}".format(journal_credit_amount[1])
                        if len(journal_credit_amount) == 2
                           and len(journal_credit_account_codes) == 2
                        else "{:.2f}".format(sum(journal_credit_amount[:-1]))
                    ).replace(".", "")

                    credit_amount_2 = str(
                        "{:.2f}".format(journal_credit_vat_amount[0])
                        if len(journal_credit_vat_amount) == 1
                        else "{:.2f}".format(credit_non_payable_amount)
                        if credit_account_code_2
                           and credit_non_payable_amount == credit_amount_1
                        else "{:.2f}".format(journal_credit_amount[0])
                        if credit_payable_account_type == "liability_payable"
                           and len(journal_credit_amount) == 2
                        else "{:.2f}".format(journal_credit_amount[0])
                        if journal.is_pos_entry
                           and journal.move_type == "entry"
                           and len(journal_credit_amount) > 2
                        else "{:.2f}".format(
                            journal_credit_amount[0] + journal_credit_amount[-1]
                        )
                        if len(journal_credit_amount) > 2
                           and "{:.2f}".format(journal_credit_amount[1]).replace(".", "")
                           == credit_amount_1
                           and journal_tax_ids
                        else "{:.2f}".format(sum(journal_credit_amount[1:]))
                        if len(journal_credit_amount) == 3
                           and credit_account_code_2
                           and journal.move_type == "in_invoice"
                        else "{:.2f}".format(sum(journal_credit_amount[:-1]))
                        if len(journal_credit_amount) > 2
                           and credit_account_code_2
                           and journal.move_type == "in_invoice"
                        else "{:.2f}".format(sum(journal_credit_amount[:-1]))
                        if len(journal_credit_amount) > 2
                           and journal.move_type == "in_invoice"
                        else "{:.2f}".format(journal_credit_amount[-1])
                        if len(journal_credit_amount) > 2
                           and journal.move_type == "out_invoice"
                           and credit_account_code_2
                        else "{:.2f}".format(journal_credit_amount[0])
                        if len(journal_credit_amount) > 2
                           and len(journal_debit_account_codes) >= 2
                           and journal.move_type == "entry"
                           and journal.is_pos_entry
                        else "{:.2f}".format(sum(journal_credit_amount[1:]))
                        if len(journal_credit_amount) > 2
                           and len(journal_debit_account_codes) >= 2
                        else "{:.2f}".format(journal_credit_amount[-1])
                        if len(journal_credit_amount) == 2
                           and len(journal_credit_account_codes) == 2
                           and journal.move_type == "in_invoice"
                        else "{:.2f}".format(journal_credit_amount[0])
                        if journal.move_type == "entry"
                           and len(journal_credit_amount) == 2
                           and len(journal_credit_account_codes) == 2
                           and journal.is_pos_entry
                        else "{:.2f}".format(journal_credit_amount[1])
                        if journal.move_type == "entry"
                           and len(journal_credit_amount) == 2
                           and len(journal_credit_account_codes) == 2
                        else "{:.2f}".format(journal_credit_amount[1])
                        if len(journal_credit_amount) == 2
                           and len(journal_credit_account_codes) == 2
                        else "{:.2f}".format(sum(journal_credit_amount[1:]))
                        if len(journal_credit_amount) > 2
                           and "{:.2f}".format(journal_credit_amount[0]).replace(".", "")
                           == credit_amount_1
                           and journal_tax_ids
                        else "{:.2f}".format(sum(journal_credit_amount[1:]))
                        if len(journal_credit_amount) == 3
                           and len(journal_credit_account_codes) == 2
                           and journal.move_type == "in_refund"
                        else "{:.2f}".format(journal_credit_amount[1])
                        if len(journal_credit_amount and journal_credit_account_codes)
                           == 2
                        else "{:.2f}".format(credit_non_payable_amount)
                        if credit_account_code_2
                        else ""
                    ).replace(".", "")

                    # Credit amount for the records which are without taxes.
                    credit_amount_3 = str(
                        int(credit_amount_1) - int(debit_amount_2)
                        if (credit_amount_1 and debit_amount_2)
                           and journal.amount_tax == 0
                        else ""
                    ).replace(".", "")

                    credit_amount_4 = str(
                        "{:.2f}".format(sum(journal_credit_amount[1:]))
                        if len(journal_credit_amount) > 2
                           and "{:.2f}".format(journal_credit_amount[0]).replace(".", "")
                           == credit_amount_1
                           and journal_tax_ids
                        else "{:.2f}".format(
                            journal_credit_amount[0] + journal_credit_amount[-1]
                        )
                        if len(journal_credit_amount) > 2
                           and "{:.2f}".format(journal_credit_amount[1]).replace(".", "")
                           == credit_amount_1
                           and journal_tax_ids
                        else ""
                    ).replace(".", "")

                    # Debit amount for POS entries
                    pos_debit_amount = str(
                        int(debit_amount_1)
                        - int(
                            str(
                                "{:.2f}".format(
                                    journal_credit_amount[-1]
                                    if len(journal_credit_amount) < 4
                                    else sum(
                                        journal_credit_amount[-3:]
                                        if len(journal_credit_amount) > 4
                                        else ""
                                    )
                                )
                            ).replace(".", "")
                        )
                        if journal.is_pos_entry
                           and journal.move_type == "entry"
                           and debit_account_code_1 in journal_credit_account_codes
                        else ""
                    )

                    pos_credit_amount = str(
                        "{:.2f}".format(
                            journal_credit_amount[3]
                            if len(journal_credit_amount) >= 4
                            else "" + journal_credit_amount[4]
                            if len(journal_credit_amount) >= 4
                            else ""
                        )
                        if journal.is_pos_entry
                           and journal.move_type == "entry"
                           and len(journal_credit_amount) > 3
                        else ""
                    ).replace(".", "")

                    pos_credit_amount_2 = str(
                        int(credit_amount_1)
                        - int(
                            str(
                                "{:.2f}".format(
                                    journal_debit_amount[1]
                                    if len(journal_debit_amount) == 3
                                    else 0
                                )
                            ).replace(".", "")
                        )
                        if journal.is_pos_entry
                           and journal.move_type == "entry"
                           and credit_account_code_1 in journal_debit_account_codes
                        else ""
                    )

                    pos_credit_amount_3 = str(
                        int(credit_amount_2 if credit_amount_2 else 0)
                        - int(debit_amount_2 if len(journal_debit_amount) == 3 else 0)
                        if journal.is_pos_entry
                           and journal.move_type == "entry"
                           and credit_account_code_1 in journal_debit_account_codes
                        else ""
                    )

                    # Withholding credit amount
                    withholding_credit_amount = (
                        "{:.2f}".format(journal_credit_amount[1])
                        if journal.move_type == "entry"
                           and journal.is_withholding
                           and len(journal_credit_account_codes) > 1
                           and len(journal_credit_amount) > 1
                        else ""
                    ).replace(".", "")

                    withholding_credit_amount_1 = (
                        "{:.2f}".format(journal_credit_amount[0])
                        if journal.origin_payment_id.receipt_id.is_credit_receipt
                           and journal.move_type == "entry"
                           and journal.is_withholding
                           and len(journal_credit_amount) > 1
                        else "{:.2f}".format(sum(journal_credit_amount))
                        if journal.move_type == "entry" and journal.is_withholding
                        else ""
                    ).replace(".", "")

                    # Debit amount for the records which are without taxes.
                    debit_amount_3 = str(
                        int(debit_amount_1) - int(credit_amount_2 or credit_amount_4)
                        if debit_amount_1
                           and (credit_amount_4 or credit_amount_2)
                           and journal.amount_tax == 0
                           and journal.move_type != "out_invoice"
                           and debit_account_code_1 != credit_account_code_1
                        else ""
                    )
                    debit_amount_4 = str(
                        debit_amount_1 if debit_amount_1 == credit_amount_3 else ""
                    )

                    # External Software Code and Receipt Credit for Credit Accounts
                    credit_payable_code = (
                        journal_credit_accounts.mapped("account_id.code")[1]
                        if credit_payable_account_type == "liability_payable"
                           and len(journal_credit_accounts.mapped("account_id.code")) > 1
                        else ""
                    )
                    receipt_credit_journal_entry = str(
                        journal.partner_id.receipt_credit
                        if journal.origin_payment_id.payment_type == "inbound"
                           and journal.partner_id.receipt_credit
                        else ""
                    )
                    receipt_credit_vendor_bill = str(
                        journal.partner_id.receipt_credit
                        if journal.move_type == "in_invoice"
                           and journal.partner_id.receipt_credit > 0
                        else journal_credit_accounts.mapped(
                            "account_id.external_software_code"
                        )[1]
                        if len(
                            journal_credit_accounts.mapped(
                                "account_id.external_software_code"
                            )
                        )
                           > 1
                           and credit_payable_account_type == "liability_payable"
                           and journal_credit_accounts.mapped(
                            "account_id.external_software_code"
                        )[1]
                           > 0
                        else credit_payable_code
                    )
                    receipt_credit_customer_credit_note = str(
                        journal.partner_id.receipt_credit
                        if journal.move_type == "out_refund"
                           and journal.partner_id.receipt_credit
                        else journal_credit_accounts.mapped(
                            "account_id.external_software_code"
                        )[1]
                        if len(
                            journal_credit_accounts.mapped(
                                "account_id.external_software_code"
                            )
                        )
                           > 1
                           and journal_credit_accounts.mapped(
                            "account_id.external_software_code"
                        )[1]
                           != 0
                           and credit_payable_account_type == "asset_receivable"
                        else ""
                    )
                    reference = (
                        journal.ref.replace("\u2066", "").replace("\u2069", "")
                        if journal.ref
                        else ""
                    )

                    custom_name = (
                        journal.origin_payment_id.receipt_id.name
                        if journal.move_type == "entry"
                           and journal.origin_payment_id.receipt_id
                        else journal.name
                             + " "
                             + str(reference)
                             + " "
                             + str(journal.partner_id.name)
                    )

                    # Define a base dictionary with the arguments that are common to both report types.
                    params = {
                        "name": name,
                        "custom_name": custom_name,
                        "journal_debit_external_software_code": journal_debit_external_software_code,
                        "journal_credit_external_software_code": journal_credit_external_software_code,
                        "receipt_debit_journal_entry": receipt_debit_journal_entry,
                        "receipt_debit_customer_invoice": receipt_debit_customer_invoice,
                        "receipt_debit_vendor_credit_note": receipt_debit_vendor_credit_note,
                        "receipt_credit_journal_entry": receipt_credit_journal_entry,
                        "receipt_credit_vendor_bill": receipt_credit_vendor_bill,
                        "receipt_credit_customer_credit_note": receipt_credit_customer_credit_note,
                        "debit_account_code_1": debit_account_code_1,
                        "debit_account_code_2": debit_account_code_2,
                        "debit_account_code_3": debit_account_code_3,
                        "withholding_debit_account_code": withholding_debit_account_code,
                        "credit_account_code_1": credit_account_code_1,
                        "credit_account_code_2": credit_account_code_2,
                        "credit_account_code_3": credit_account_code_3,
                        "withholding_credit_account_code": withholding_credit_account_code,
                        "debit_amount_1": debit_amount_1,
                        "debit_amount_2": debit_amount_2,
                        "credit_amount_1": credit_amount_1,
                        "credit_amount_2": credit_amount_2,
                        "withholding_debit_amount": withholding_debit_amount,
                        "withholding_debit_amount_1": withholding_debit_amount_1,
                        "withholding_credit_amount": withholding_credit_amount,
                        "withholding_credit_amount_1": withholding_credit_amount_1,
                        "credit_amount_3": credit_amount_3,
                        "credit_amount_4": credit_amount_4
                    }

                    # If HRP, calculate and add HRP‐specific parameters
                    if _is_for_hrp:
                        # Initialize dictionaries to store debit and credit totals by account
                        account_totals = {}
                        vat_account_totals = {}

                        # Combine processing of debit and credit lines into a single loop
                        for line in journal.line_ids:
                            account = (
                                line.account_id.code
                            )  # Use account code for identification
                            if line.debit > 0:  # Accumulate debit amounts
                                if account not in account_totals:
                                    account_totals[account] = {"debit": 0, "credit": 0}
                                account_totals[account]["debit"] += round(line.debit, 2)
                            if line.credit > 0:  # Accumulate credit amounts
                                if account not in account_totals:
                                    account_totals[account] = {"debit": 0, "credit": 0}
                                account_totals[account]["credit"] += round(line.credit, 2)

                            if line.account_id:
                                if "VAT" in line.account_id.name or account.startswith(
                                        "111"
                                ):
                                    if account not in vat_account_totals:
                                        vat_account_totals[account] = {
                                            "debit": 0,
                                            "credit": 0,
                                        }
                                    if line.debit > 0:  # Accumulate debit amounts
                                        vat_account_totals[account][
                                            "debit"
                                        ] += round(line.debit, 2)
                                    if line.credit > 0:  # Accumulate credit amounts
                                        vat_account_totals[account][
                                            "credit"
                                        ] += round(line.credit, 2)

                        # Process and prepare results
                        total_credit = 0
                        net_debit = 0
                        specific_net_credit = 0
                        vat_net_credit = 0

                        for account in account_totals.keys():
                            if account not in vat_account_totals.keys():
                                net_debit += account_totals[account]["debit"]
                                specific_net_credit += account_totals[account]["credit"]
                            else:
                                vat_net_credit += account_totals[account]["credit"]

                        net_debit = str("{:.2f}".format(max(0, net_debit))).replace('.', '')
                        specific_net_credit = str("{:.2f}".format(max(0, specific_net_credit))).replace('.', '')
                        vat_net_credit = str("{:.2f}".format(max(0, vat_net_credit))).replace('.', '')

                        # for account, totals in account_totals.keys():
                        #     total_debit = totals["debit"]
                        #     total_credit = totals["credit"]
                        #     net_debit = str(
                        #         "{:.2f}".format(max(0, total_debit - total_credit))
                        #     ).replace(".", "")
                        #     net_credit = max(0, total_credit - total_debit)
                        #     if net_credit > 0:
                        #         specific_net_credit = str(
                        #             "{:.2f}".format(net_credit)
                        #         ).replace(".", "")
                        #
                        # for account, totals in vat_account_totals.items():
                        #     total_debit = totals["debit"]
                        #     total_credit = totals["credit"]
                        #     vat_net_debit = max(0, total_debit - total_credit)
                        #     vat_net_credit = str(
                        #         "{:.2f}".format(max(0, total_credit - total_debit))
                        #     ).replace(".", "")

                        debit_1_for_hrp = str(
                            "{:.2f}".format(journal.amount_untaxed)
                            if journal.move_type
                               in ("in_invoice", "in_refund", "out_refund")
                            else ""
                        ).replace(".", "")

                        credit_1_for_hrp = str(
                            "{:.2f}".format(journal.amount_untaxed)
                            if (credit_amount_1 and debit_amount_2)
                               and journal.move_type in ("out_invoice", "out_refund")
                            else ""
                        ).replace(".", "")

                        params.update({
                            "net_debit": net_debit,
                            "specific_net_credit": specific_net_credit,
                            "vat_net_credit": vat_net_credit,
                            "debit_1_for_hrp": debit_1_for_hrp,
                            "credit_1_for_hrp": credit_1_for_hrp,
                            # More parameters that could be used in HRP logic:
                            "journal_debit_accounts": journal_debit_accounts,
                            "journal_credit_account_codes": journal_credit_account_codes,
                            "journal_debit_amount": journal_debit_amount,
                            "journal_credit_amount": journal_credit_amount,
                            "journal_tax_ids": journal_tax_ids,
                            "pos_credit_amount": pos_credit_amount,
                        })

                        if journal.is_pos_entry:
                            _logger.info(f"\nAccount and VAT totals: {account_totals}, \n{vat_account_totals}\n")

                        if _is_for_rivhit:
                            journal_data = self._prepare_journal_data(journal, "rivhit", params)
                        elif _is_for_hrp:
                            journal_data = self._prepare_journal_data(journal, "hrp", params)

                docs.append(journal_data)
        return docs

    def _prepare_journal_data(self, journal, report_type, params):
        # Initialize type-determining indicators
        is_rivhit = (report_type == "rivhit")
        is_hrp = (report_type == "hrp")
        if not is_rivhit and not is_hrp:
            raise ValueError(f"Unknown report type: {report_type}")

        # ----------------------------------
        # 1) EXTRACT AND INITIALIZE SHARED OR SIMILAR VARIABLES
        # ----------------------------------
        if is_rivhit:
            date_fmt = "%d/%m/%y"
            date_len = 8
            movement_code_val = str(journal.movement_code)
            account_field_width = 9
        else:  # HRP
            date_fmt = "%d/%m/%Y"
            date_len = 10
            movement_code_val = str(journal.movement_code_string)
            account_field_width = 15

        date_str = journal.date.strftime(date_fmt)
        validity_str = journal.invoice_date_due.strftime(date_fmt)

        name = params.get("name", "")
        custom_name = params.get("custom_name", "")
        journal_debit_external_software_code = params.get("journal_debit_external_software_code", 0)
        journal_credit_external_software_code = params.get("journal_credit_external_software_code", 0)
        receipt_debit_journal_entry = params.get("receipt_debit_journal_entry", "")
        receipt_debit_customer_invoice = params.get("receipt_debit_customer_invoice", "")
        receipt_debit_vendor_credit_note = params.get("receipt_debit_vendor_credit_note", "")
        receipt_credit_journal_entry = params.get("receipt_credit_journal_entry", "")
        receipt_credit_vendor_bill = params.get("receipt_credit_vendor_bill", "")
        receipt_credit_customer_credit_note = params.get("receipt_credit_customer_credit_note", "")
        debit_account_code_1 = params.get("debit_account_code_1", "")
        debit_account_code_2 = params.get("debit_account_code_2", "")
        debit_account_code_3 = params.get("debit_account_code_3", "")
        withholding_debit_account_code = params.get("withholding_debit_account_code", "")
        credit_account_code_1 = params.get("credit_account_code_1", "")
        credit_account_code_2 = params.get("credit_account_code_2", "")
        credit_account_code_3 = params.get("credit_account_code_3", "")
        withholding_credit_account_code = params.get("withholding_credit_account_code", "")
        debit_amount_1 = params.get("debit_amount_1", "")
        debit_amount_2 = params.get("debit_amount_2", "")
        credit_amount_1 = params.get("credit_amount_1", "")
        credit_amount_2 = params.get("credit_amount_2", "")
        withholding_debit_amount = params.get("withholding_debit_amount", "")
        withholding_debit_amount_1 = params.get("withholding_debit_amount_1", "")
        withholding_credit_amount = params.get("withholding_credit_amount", "")
        withholding_credit_amount_1 = params.get("withholding_credit_amount_1", "")
        credit_amount_3 = params.get("credit_amount_3", "")
        debit_amount_3 = params.get("debit_amount_3", "")
        debit_amount_4 = params.get("debit_amount_4", "")

        # HRP-specific parameters (default is empty so no error in rivhit)
        net_debit = params.get("net_debit", "")
        specific_net_credit = params.get("specific_net_credit", "")
        vat_net_credit = params.get("vat_net_credit", "")
        debit_1_for_hrp = params.get("debit_1_for_hrp", "")
        credit_1_for_hrp = params.get("credit_1_for_hrp", "")
        journal_debit_accounts = params.get("journal_debit_accounts")
        journal_credit_account_codes = params.get("journal_credit_account_codes")
        journal_debit_amount = params.get("journal_debit_amount")
        journal_credit_amount = params.get("journal_credit_amount")
        journal_tax_ids = params.get("journal_tax_ids")
        pos_credit_amount = params.get("pos_credit_amount", "")

        # --------------------------------------------------
        # 2) BUILD THE COMMON FIELDS FOR BOTH RIVHIT AND HRP
        # --------------------------------------------------
        journal_data = {
            "movement_code": self.format_string(movement_code_val, 3, "0"),
            "name": self.format_string(name if "/" in journal.name else journal.name, 9),
            "account_date": self.format_string(date_str, date_len),
            "reference": self.format_string("", 9),
            "validity_date": self.format_string(validity_str, date_len),
            "מטבע": self.format_string("1", 3),
            "custom_name": self.format_string(custom_name or "", 50),
        }

        # --------------------------------------
        # 3) LOGIC FOR DEBIT/CREDIT ACCOUNT FIELDS
        # --------------------------------------

        # ============== debit_account1 ==============
        if is_rivhit:
            debit_acc_1_val = (
                    receipt_debit_journal_entry
                    or receipt_debit_customer_invoice
                    or receipt_debit_vendor_credit_note
                    or (
                        str(journal_debit_external_software_code) if journal_debit_external_software_code != 0 else debit_account_code_1)
            )
        else:  # HRP
            if (journal_debit_external_software_code != 0
                    and debit_account_code_1
                    and journal_debit_accounts
                    and debit_account_code_1 == journal_debit_accounts.mapped("account_id.code")[0]):
                fallback_val = str(journal_debit_external_software_code)
            else:
                fallback_val = debit_account_code_1

            debit_acc_1_val = (
                    receipt_debit_journal_entry
                    or receipt_debit_customer_invoice
                    or receipt_debit_vendor_credit_note
                    or fallback_val
            )

        journal_data["debit_account1"] = self.format_string(debit_acc_1_val, account_field_width, align="left")

        # ============== debit_account2 ==============
        if is_rivhit:
            debit_acc_2_val = (
                    withholding_debit_account_code
                    or (
                        debit_account_code_2
                        if (debit_account_code_2 and journal.amount_tax != 0)
                        else (
                            debit_account_code_3
                            if (debit_account_code_3 and journal.amount_tax != 0)
                            else ""
                        )
                    )
            )
        else:  # HRP
            if withholding_debit_account_code:
                debit_acc_2_val = withholding_debit_account_code
            elif journal.is_pos_entry and journal.move_type == "entry" and debit_amount_2 != pos_credit_amount:
                debit_acc_2_val = ""
            elif debit_account_code_2 and journal.amount_tax != 0 and journal.move_type not in "out_invoice":
                debit_acc_2_val = debit_account_code_2
            elif debit_account_code_3 and journal.amount_tax != 0 and journal.move_type not in (
                    "out_invoice", "out_refund"):
                debit_acc_2_val = debit_account_code_3
            else:
                debit_acc_2_val = ""

        journal_data["debit_account2"] = self.format_string(debit_acc_2_val, account_field_width, align="left")

        # ============== credit_account1 ==============
        if is_rivhit:
            credit_acc_1_val = (
                    receipt_credit_journal_entry
                    or receipt_credit_vendor_bill
                    or receipt_credit_customer_credit_note
                    or (
                        str(journal_credit_external_software_code) if journal_credit_external_software_code != 0 else credit_account_code_1)
            )
        else:
            # HRP
            if journal_credit_external_software_code != 0:
                fallback_val = str(journal_credit_external_software_code)
            else:
                fallback_val = credit_account_code_1

            credit_acc_1_val = (
                    receipt_credit_journal_entry
                    or receipt_credit_vendor_bill
                    or receipt_credit_customer_credit_note
                    or fallback_val
            )

        journal_data["credit_account1"] = self.format_string(credit_acc_1_val, account_field_width, align="left")

        # ============== credit_account2 ==============
        if is_rivhit:
            credit_acc_2_val = (
                    withholding_credit_account_code
                    or (
                        credit_account_code_2
                        if (credit_account_code_2 and journal.amount_tax != 0)
                        else (
                            credit_account_code_3
                            if (credit_account_code_3 and not journal_tax_ids and journal.amount_tax != 0)
                            else ""
                        )
                    )
            )
        else:
            # HRP
            if withholding_credit_account_code:
                credit_acc_2_val = withholding_credit_account_code
            elif credit_account_code_2 and journal.amount_tax != 0 and journal.move_type not in (
                    "in_invoice", "in_refund"):
                credit_acc_2_val = credit_account_code_2
            elif credit_account_code_3 and journal.amount_tax != 0 and journal.move_type not in (
                    "in_invoice", "in_refund"):
                credit_acc_2_val = credit_account_code_3
            elif journal.is_pos_entry and journal.move_type == "entry" and journal_credit_account_codes and len(
                    journal_credit_account_codes) > 2:
                credit_acc_2_val = credit_account_code_2
            elif journal.is_pos_entry and journal.move_type == "entry" and credit_account_code_3 != credit_account_code_1:
                credit_acc_2_val = credit_account_code_3
            else:
                credit_acc_2_val = ""

        journal_data["credit_account2"] = self.format_string(credit_acc_2_val, account_field_width, align="left")

        # ------------------------------------------------------
        # 4) LOGIC FOR DEBIT AMOUNTS AND CREDIT AMOUNTS (RIVHIT VS. HRP)
        # ------------------------------------------------------
        if is_rivhit:
            # ====================
            # RIVHIT AMOUNT FIELDS
            # ====================
            journal_data["debit_amount_1"] = self.format_string(
                str(
                    withholding_debit_amount_1
                    or (
                        (debit_amount_4 or debit_amount_3)
                        if (debit_amount_4 or debit_amount_3) and not journal_tax_ids and journal.amount_tax == 0
                        else debit_amount_1
                    )
                ),
                10,
            )
            journal_data["debit_amount_2"] = self.format_string(
                str(
                    withholding_debit_amount
                    or (debit_amount_2 if debit_amount_2 and journal.amount_tax != 0 else "")
                ),
                10,
            )
            journal_data["credit_amount_1"] = self.format_string(
                str(
                    withholding_credit_amount_1
                    or (
                        credit_amount_3
                        if credit_amount_3 and not journal_tax_ids and journal.amount_tax == 0
                        else credit_amount_1
                    )
                ),
                10,
            )
            journal_data["credit_amount_2"] = self.format_string(
                str(
                    withholding_credit_amount
                    or (credit_amount_2 if credit_amount_2 and journal.amount_tax != 0 else "")
                ),
                10,
            )

        else:
            # ================
            # HRP AMOUNT FIELDS
            # ================
            # We'll reuse your existing logic for net_debit, specific_net_credit, etc.
            journal_data["debit_amount_1"] = self.format_string(
                str(
                    net_debit if net_debit and int(net_debit) > 0 and journal.is_pos_entry
                    else (
                            withholding_debit_amount_1
                            or (
                                "-" + str(debit_1_for_hrp)
                                if journal.move_type in ("in_refund", "out_refund") and debit_1_for_hrp
                                else (
                                    debit_1_for_hrp
                                    if debit_1_for_hrp and journal.amount_tax != 0
                                    else (
                                        (debit_amount_4 or debit_amount_3)
                                        if (
                                                   debit_amount_4 or debit_amount_3) and not journal_tax_ids and journal.amount_tax == 0
                                        else (debit_amount_1 or "")
                                    )
                                )
                            )
                    )
                ),
                10,
            )
            journal_data["debit_amount_2"] = self.format_string(
                str(
                    withholding_debit_amount
                    or (
                        "-" + str(debit_amount_2)
                        if debit_amount_2 and journal.amount_tax != 0 and journal.move_type in (
                            "out_refund", "in_refund")
                        else (
                            debit_amount_2
                            if debit_amount_2 and journal.amount_tax != 0 and journal.move_type not in ("out_invoice")
                            else (
                                debit_amount_2
                                if journal.is_pos_entry
                                   and journal.move_type == "entry"
                                   and debit_amount_2 != pos_credit_amount
                                   and (not journal_debit_amount or len(journal_debit_amount) <= 3)
                                else ""
                            )
                        )
                    )
                ),
                10,
            )
            journal_data["credit_amount_1"] = self.format_string(
                str(
                    specific_net_credit
                    if specific_net_credit and int(specific_net_credit) > 0 and journal.is_pos_entry
                    else (
                            withholding_credit_amount_1
                            or (
                                "-" + str(credit_1_for_hrp)
                                if (
                                        journal.move_type in ("in_refund", "out_refund")
                                        and credit_1_for_hrp
                                        and journal_credit_amount
                                        and len(journal_credit_amount) > 1
                                        and journal_credit_account_codes
                                        and len(journal_credit_account_codes) > 1
                                )
                                else (
                                    credit_1_for_hrp
                                    if credit_1_for_hrp
                                       and journal_credit_amount
                                       and len(journal_credit_amount) > 1
                                       and journal_credit_account_codes
                                       and len(journal_credit_account_codes) > 1
                                    else (
                                        "-" + str(credit_amount_3)
                                        if credit_amount_3 and not journal_tax_ids and journal.amount_tax == 0 and journal.move_type == "in_refund"
                                        else (
                                            credit_amount_3
                                            if credit_amount_3 and not journal_tax_ids and journal.amount_tax == 0
                                            else (
                                                "-" + str(credit_amount_1)
                                                if credit_amount_1 and journal.move_type == "in_refund"
                                                else credit_amount_1 or ""
                                            )
                                        )
                                    )
                                )
                            )
                    )
                ),
                10,
            )
            journal_data["credit_amount_2"] = self.format_string(
                str(
                    vat_net_credit
                    if vat_net_credit
                       and int(vat_net_credit) > 0
                       and journal_credit_account_codes
                       and len(journal_credit_account_codes) > 1
                       and journal.is_pos_entry
                    else (
                            withholding_credit_amount
                            or (
                                credit_amount_2
                                if credit_amount_2
                                   and journal.amount_tax != 0
                                   and journal.move_type not in ("in_invoice", "in_refund")
                                   and not journal.is_pos_entry
                                else (
                                    credit_amount_2
                                    if journal.is_pos_entry
                                       and journal.move_type == "entry"
                                       and journal_credit_account_codes
                                       and len(journal_credit_account_codes) > 2
                                    else ""
                                )
                            )
                    )
                ),
                10,
            )

        return journal_data

    def get_document_vals_movein_prm(self):
        docs = []
        movein_prm_data = {}
        _is_for_rivhit, _is_for_hrp = self._get_self_indicators()
        if _is_for_rivhit:
            movein_prm_data = {
                "1": "187 ;גודל הרשומה",
                "2": "1 3 ;קוד סוג תנועה",
                "3": "5 13 ;אסמכתא",
                "4": "24 32;אסמכתא 2",
                "5": "15 22 ;תאריך אסמכתא",
                "6": "34 41 ;תאריך ערך",
                "7": "0 0 ;תמחיר",
                "8": "43	45 ;קוד מטבע",
                "9": "47 96 ;פרוט",
                "10": "98	106 ;מס חשבון חובה 1",
                "11": "108 116 ;מס חשבון חובה 2",
                "12": "118 126 ;מס חשבון זכות 1",
                "13": "128 136 ;מס חשבון זכות 2",
                "14": '138 148 ;סכום חובה 1 בש"ח',
                "15": '150 160 ;סכום חובה 2 בש"ח',
                "16": '162 172 ;סכום זכות 1 בש"ח',
                "17": '174 184 ;סכום זכות 2 בש"ח',
                "18": '0 0 ;סכום חובה 1 מט"ח',
                "19": '0 0 ;סכום חובה 2 מט"ח',
                "20": '0 0 ;סכום זכות 1 מט"ח',
                "21": '0 0 ;סכום זכות 2 מט"ח',
                "22": "0 0 ;תאריך שלישי",
                "23": "0 0 ;אסמכתא 3",
                "24": "0 0 ;כמות",
                "25": "0 0 ;קובץ",
                "26": "0 0 ;הערות נוספות",
                "27": "0 0 ;הערות נוספות 2",
                "28": "0 0 ;סניף",
                "29": "0 0 ;מספר ע.מ",
            }
        elif _is_for_hrp:
            movein_prm_data = {
                "1": "211 ;גודל הרשומה",
                "2": "1 3 ;קוד סוג תנועה",
                "3": "5 14 ;אסמכתא",
                "4": "26 35;אסמכתא 2",
                "5": "15 25;תאריך אסמכתא",
                "6": "36 46 ;תאריך ערך",
                "7": "0 0 ;תמחיר",
                "8": "47	50 ;קוד מטבע",
                "9": "51 101 ;פרוט",
                "10": "102	117 ;מס חשבון חובה 1",
                "11": "118 133 ;מס חשבון חובה 2",
                "12": "134 149 ;מס חשבון זכות 1",
                "13": "150 165 ;מס חשבון זכות 2",
                "14": '166 176 ;סכום חובה 1 בש"ח',
                "15": '177 187 ;סכום חובה 2 בש"ח',
                "16": '188 198 ;סכום זכות 1 בש"ח',
                "17": '199 209 ;סכום זכות 2 בש"ח',
                "18": '0 0 ;סכום חובה 1 מט"ח',
                "19": '0 0 ;סכום חובה 2 מט"ח',
                "20": '0 0 ;סכום זכות 1 מט"ח',
                "21": '0 0 ;סכום זכות 2 מט"ח',
                "22": "0 0 ;תאריך שלישי",
                "23": "0 0 ;אסמכתא 3",
                "24": "0 0 ;כמות",
                "25": "0 0 ;קובץ",
                "26": "0 0 ;הערות נוספות",
                "27": "0 0 ;הערות נוספות 2",
                "28": "0 0 ;סניף",
                "29": "0 0 ;מספר ע.מ",
            }
        docs.append(movein_prm_data)
        return docs

    def generate(self):
        _is_for_rivhit, _is_for_hrp = self._get_self_indicators()
        content = (
            etree.fromstring(
                self.env["ir.ui.view"]._render_template(
                    "bizzup_movein_report.movein_dat_file",
                    {"docs_list": self.get_document_vals()},
                )
            )
            .text.replace("\n            ", "\t")
            .replace("!@#*^$", "\n")
            .replace("\n", "")
            .replace("$^*#@!", " \t ")
            .replace("		", "\n")
            .strip()
            .encode("iso8859_8")
        )
        movein_prn_content = (
            etree.fromstring(
                self.env["ir.ui.view"]._render_template(
                    "bizzup_movein_report.movein_prm_file",
                    {"docs_list": self.get_document_vals_movein_prm()},
                )
            )
            .text.replace("\n            ", "\t")
            .replace("!@#*^$", "\n")
            .replace("\n", "")
            .replace("$^*#@!", " \t ")
            .replace("		", "\n")
            .strip()
            .encode("iso8859_8")
        )

        # content = re.sub(' \t ', '', content)
        if _is_for_rivhit or _is_for_hrp:
            vals = {
                "state": "get",
                "movein_data": base64.encodebytes(content),
                "movein_filename": "movein.dat" if _is_for_rivhit else "movein.doc",
                "movein_prm_data": base64.encodebytes(movein_prn_content),
                "movein_prm_filename": "movein.prm",
            }
            self.write(vals)
        else:
            raise ValidationError(
                _("Please select the type of the report from Settings.")
            )
        return {
            "type": "ir.actions.act_window",
            "res_model": "movein.report.wizard",
            "view_mode": "form",
            "res_id": self.id,
            "views": [(False, "form")],
            "target": "new",
        }
