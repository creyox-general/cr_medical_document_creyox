from odoo.addons.bizzup_movein_report.models.calc_helper import CalcHelper
import logging

_logger = logging.getLogger(__name__)

class CreditCalcHelper(CalcHelper):
    def __init__(self, journal, debit_helper, is_for_rivhit):
        super().__init__(journal)
        self.currency_name = journal.currency_id.name
        self.is_for_rivhit = is_for_rivhit
        self.debit_account_1 = debit_helper.get_debit_account_code_1()
        self.debit_amount_1 = debit_helper.get_debit_amount_1()
        self.debit_amount_2 = debit_helper.get_debit_amount_2()
        self.debit_amounts = debit_helper.debit_amounts

        # Initialize own filtered fields
        self._initialize_fields()

        _logger.info(f"CREDIT ROW NEWLY INITIALIZED NAME AS: {self.name}")

    def _initialize_fields(self):
        """Initialize and cache necessary fields for calculations."""
        # Filter tax IDs
        self.journal_tax_ids = self.journal.invoice_line_ids.filtered(
            lambda line: line.tax_ids and (tax.amount == 0 for tax in line.tax_ids))

        # Filter credit accounts
        self.journal_credit_accounts = self.journal.line_ids.filtered(lambda line: line.credit > 0)

        # Ensure self.journal_credit_accounts is an Odoo recordset
        if not self.journal_credit_accounts:
            self.journal_credit_accounts = self.journal.line_ids.browse([])  # Empty recordset

        # Filter VAT accounts within credit accounts
        self.journal_credit_vat_accounts = self.journal_credit_accounts.filtered(
            lambda line: str(line.account_id.code).startswith('111') or ""
        )

        # Map required fields
        self.credit_account_codes = self.journal_credit_accounts.mapped("account_id.code") or []
        self.credit_account_types = self.journal_credit_accounts.mapped("account_id.account_type") or []
        self.credit_external_codes = self.journal_credit_accounts.mapped("account_id.external_software_code") or []
        self.credit_vat_account_codes = self.journal_credit_vat_accounts.mapped("account_id.code") or []
        self.credit_amounts = self.journal_credit_accounts.mapped("credit") or []
        self.credit_vat_amounts = self.journal_credit_vat_accounts.mapped("credit") or []
        self.credit_external_software_code = self.credit_external_codes[0] or ""

    def get_credit_payable_account_type(self):
        """Get the payable account type from credit accounts."""
        if self.credit_account_types:
            return self.credit_account_types[1] if len(self.credit_account_types) > 1 else self.credit_account_types[0]
        return ""

    def get_credit_non_payable_account_type(self):
        """Get the non-payable account type from credit accounts."""
        return self.credit_account_types[0] if self.credit_account_types else ""

    def get_credit_non_payable_account_code(self):
        """Get the non-payable account code from credit accounts."""
        if self.get_credit_non_payable_account_type() != "liability_payable" and self.credit_external_codes:
            if self.credit_external_codes[0] > 0:
                return str(self.credit_external_codes[0])
        return ""

    def get_external_code(self):
        """Get the external code for credit accounts."""
        if self.get_credit_non_payable_account_code() and len(self.credit_external_codes) == 2:
            return self.get_credit_non_payable_account_code()
        elif self.move_type in ("in_invoice", "out_invoice", "out_refund") and len(self.credit_account_codes) == 2:
            if self.get_credit_payable_account_type() != "liability_payable" and len(self.credit_external_codes) == 2:
                return str(self.credit_external_codes[1])
        return ""

    def get_credit_account_code_1(self):
        """Calculate credit_account_code_1 based on conditions."""
        # Check POS entry conditions first (priority-wise)
        if self.credit_account_codes:
            if self.journal.is_pos_entry and self.move_type == 'entry' and len(
                    self.credit_account_codes) >= 2:
                if self.debit_account_1 and self.credit_account_codes[1] == self.debit_account_1:
                    return str(self.credit_account_codes[0])
                else:
                    return str(self.credit_account_codes[1])

        if self.credit_account_codes:
            if len(self.credit_account_codes) == 2 and self.move_type == "out_invoice":
                if self.credit_vat_account_codes and self.credit_account_codes[0] == self.credit_vat_account_codes[0]:
                    return str(self.credit_account_codes[1])
            return str(self.credit_account_codes[0])

        return ""

    def get_credit_account_code_2(self):
        """Calculate credit_account_code_2 based on conditions."""
        external_code = self.get_external_code()
        if self.credit_external_software_code and int(self.credit_external_software_code) != 0:
            return str(self.credit_external_software_code)
        if len(self.credit_account_codes) == 1 and self.credit_vat_account_codes:
            return str(self.credit_vat_account_codes[0])
        if len(self.credit_account_codes) > 1:
            non_payable_code = self.get_credit_non_payable_account_code()
            if non_payable_code and self.get_credit_account_code_1() != self.credit_account_codes[0]:
                return non_payable_code
        if external_code:
            return external_code
        if self.move_type in ('in_invoice', 'out_invoice', 'entry', 'in_refund') and len(
                self.credit_account_codes) == 2:
            if self.get_credit_payable_account_type() != 'liability_payable':
                return str(self.credit_account_codes[1])
        if self.journal.is_pos_entry and self.move_type == 'entry' and len(
                self.credit_account_codes) > 2:
            return str(self.credit_account_codes[0])
        return ""

    def get_credit_extra_code(self):
        """Get the extra credit account code."""
        if len(self.credit_amounts) == 2 and len(self.credit_account_codes) == 2:
            return str(self.credit_account_codes[1])
        return ""

    def get_credit_account_code_3(self):
        """Calculate credit_account_code_3 based on conditions."""
        credit_extra_code = self.get_credit_extra_code()
        credit_account_code_1 = self.get_credit_account_code_1()
        if credit_account_code_1 == credit_extra_code:
            return str(self.credit_account_codes[0])
        elif len(self.credit_amounts) == 2 and len(self.credit_account_codes) == 2:
            return credit_account_code_1
        return ""

    def get_withholding_credit_account_code(self):
        """Calculate withholding_credit_account_code based on conditions."""
        if self.move_type == "entry" and self.is_withholding and len(self.credit_account_codes) > 1:
            return str(self.credit_account_codes[1])
        return ""

    def _get_credit_non_payable_amount(self):
        """Get the amount for non-payable accounts."""
        if self.get_credit_non_payable_account_type() != "liability_payable" and self.credit_amounts:
            return self.credit_amounts[0]
        return 0

    def get_credit_amount_1(self):
        """Calculate credit_amount_1 based on conditions."""
        amounts = self.credit_amounts  # equivalent to journal_credit_amount
        cp_type = self.get_credit_payable_account_type()  # credit_payable_account_type
        if not amounts:
            computed_amount = 0
        else:
            if len(amounts) > 2 and self.credit_vat_amounts and self.journal.amount_tax != 0:
                computed_amount = sum(amounts[:-1])
            elif len(self.credit_account_codes) > 1 and len(amounts) < 2:
                computed_amount = amounts[1]
            elif len(amounts) == 2 and cp_type == 'liability_payable':
                computed_amount = amounts[1]
            elif len(amounts) > 2 and cp_type == 'liability_payable' and self.move_type == 'in_invoice' and self.currency_name == 'GBP':
                computed_amount = amounts[1]
            elif len(amounts) > 2 and cp_type == 'liability_payable':
                computed_amount = amounts[-1]
            elif len(amounts) > 2 and len(self.credit_account_codes) == 2 and cp_type == 'liability_payable':
                computed_amount = amounts[1]
            elif len(amounts) >= 2 and self.move_type == 'out_invoice' and self.journal.amount_tax == 0:
                computed_amount = self.journal.amount_total
            elif len(self.credit_account_codes) == 1 and self.move_type != 'out_refund':
                computed_amount = sum(amounts)
            elif len(amounts) > 2 and self.move_type == 'in_invoice' and self.is_for_rivhit:
                computed_amount = self.journal.amount_total
            elif len(amounts) == 3 and len(self.credit_account_codes) == 2 and self.move_type == 'in_invoice':
                computed_amount = amounts[0]
            elif len(amounts) > 2 and self.move_type == 'in_invoice':
                computed_amount = amounts[-1]
            elif self.move_type == 'out_refund' and len(amounts) == 1 and len(self.credit_account_codes) == 1:
                computed_amount = amounts[0]
            elif self.move_type == 'out_refund' and self.journal.amount_tax != 0:
                computed_amount = -self.journal.amount_untaxed
            elif len(amounts) == 2 and self.move_type == 'out_refund' and cp_type != 'liability_payable':
                computed_amount = amounts[-1]
            elif len(amounts) > 2 and self.move_type == 'out_invoice' and not self.debit_amount_2:
                computed_amount = sum(amounts)
            elif len(amounts) == 4 and len(self.credit_account_codes) >= 2 and self.move_type == 'in_refund':
                computed_amount = amounts[-1]
            elif len(amounts) > 3 and len(self.credit_account_codes) > 3 and self.journal.is_pos_entry and self.move_type == 'entry':
                computed_amount = amounts[1] + amounts[2]
            elif len(amounts) == 2 and len(self.credit_account_codes) == 2 and self.journal.is_pos_entry and self.move_type == 'entry':
                computed_amount = amounts[1]
            elif len(amounts) == 3 and len(self.credit_account_codes) == 3 and self.journal.is_pos_entry and self.move_type == 'entry':
                computed_amount = sum(amounts[1:])
            elif len(amounts) >= 2 and len(self.credit_account_codes) >= 2:
                computed_amount = amounts[0]
            elif len(amounts) == 2 and len(self.credit_account_codes) == 2:
                computed_amount = amounts[1]
            else:
                computed_amount = sum(amounts[:-1])
        # Format the computed amount as a number with two decimals and remove the dot.
        return "{:.2f}".format(computed_amount).replace(".", "")

    def get_credit_amount_2(self):
        """Calculate credit_amount_2 based on conditions."""
        amounts = self.credit_amounts
        amount = 0
        if self.credit_vat_amounts:
            amount = sum(self.credit_vat_amounts)
        elif self.get_credit_non_payable_account_code() and self._get_credit_non_payable_amount() == self.get_credit_amount_1():
            amount = self._get_credit_non_payable_amount()
        elif len(amounts) == 2:
            if self.get_credit_payable_account_type() == "liability_payable":
                amount = amounts[0]
            else:
                amount = amounts[1]
        elif len(amounts) > 2 and self.get_credit_account_code_2():
            if "{:.2f}".format(amounts[1]).replace(".", "") == self.get_credit_amount_1():
                amount = amounts[0] + amounts[-1]
            elif self.move_type == "in_invoice":
                amount = sum(amounts[:-1])
            elif self.move_type == "out_invoice":
                amount = amounts[-1]
            else:
                amount = sum(amounts[1:])
        return "{:.2f}".format(amount).replace(".", "")

    def get_credit_amount_3(self):
        """Calculate credit_amount_3 for records without taxes."""
        if self.get_credit_amount_1() and self.debit_amount_2 and self.journal_tax_ids:
            if self.move_type not in ("entry", "in_refund"):
                amount = int(self.get_credit_amount_1()) - int(self.debit_amount_2)
                return str(amount).replace(".", "")
            elif self.move_type == "in_refund" and self.is_for_rivhit:
                debit_amount = self.debit_amount_2 if self.debit_amount_2 != self.debit_amount_1 else "{:.2f}".format(
                    self.debit_amounts[0]).replace(".", "")
                amount = int(self.get_credit_amount_1()) - int(debit_amount)
                return str(amount).replace(".", "")
        return ""

    def get_credit_amount_4(self):
        """Calculate credit_amount_4 based on conditions."""
        amounts = self.credit_amounts
        if len(amounts) > 2 and self.journal_tax_ids:
            if "{:.2f}".format(amounts[0]).replace(".", "") == self.get_credit_amount_1():
                amount = sum(amounts[1:])
                return "{:.2f}".format(amount).replace(".", "")
            elif "{:.2f}".format(amounts[1]).replace(".", "") == self.get_credit_amount_1():
                amount = amounts[0] + amounts[-1]
                return "{:.2f}".format(amount).replace(".", "")
        return ""

    def get_withholding_credit_amount(self):
        """Calculate withholding_credit_amount based on conditions."""
        if self.move_type == "entry" and self.is_withholding and len(self.credit_account_codes) > 1 and len(
                self.credit_amounts) > 1:
            amount = self.credit_amounts[1]
            return "{:.2f}".format(amount).replace(".", "")
        return ""

    def get_withholding_credit_amount_1(self):
        """Calculate withholding_credit_amount_1 based on conditions."""
        if self.move_type == "entry" and self.is_withholding:
            if self.payment_id and self.payment_id.receipt_id and self.payment_id.receipt_id.is_credit_receipt and len(
                    self.credit_amounts) > 1:
                amount = self.credit_amounts[0]
            else:
                amount = sum(self.credit_amounts)
            return "{:.2f}".format(amount).replace(".", "")
        return ""

    def get_debit_amount_3(self):
        """Calculate debit_amount_3 for records without taxes."""
        if self.debit_amount_1 and (self.get_credit_amount_4() or self.get_credit_amount_2()) and self.journal_tax_ids:
            if self.move_type not in ("out_invoice", "entry"):
                credit_amount = self.get_credit_amount_2() or self.get_credit_amount_4()
                amount = int(self.debit_amount_1) - int(credit_amount)
                return str(abs(amount)).replace("-", "")
        return ""

    def get_debit_amount_4(self):
        """Calculate debit_amount_4 based on conditions."""
        if self.debit_amount_1 == self.get_credit_amount_3():
            return self.debit_amount_1
        return ""

    def get_receipt_credit_journal_entry(self):
        """Calculate receipt_credit_journal_entry based on conditions."""
        if self.payment_id and self.payment_id.payment_type == "inbound" and self.partner_id.receipt_credit:
            return str(self.partner_id.receipt_credit)
        return ""

    def get_receipt_credit_vendor_bill(self):
        """Calculate receipt_credit_vendor_bill based on conditions."""
        if self.move_type == "in_invoice":
            if self.partner_id.receipt_credit > 0:
                return str(self.partner_id.receipt_credit)
            elif len(self.credit_external_codes) > 1 and int(self.credit_external_codes[1]) > 0:
                if self.get_credit_payable_account_type() == "liability_payable":
                    return str(self.credit_external_codes[1])
            elif self.get_credit_payable_code():
                return self.get_credit_payable_code()
        return ""

    def get_credit_payable_code(self):
        """Get the payable code from credit accounts."""
        if self.get_credit_payable_account_type() == "liability_payable" and len(self.credit_account_codes) > 1:
            return str(self.credit_account_codes[1])
        return ""

    def get_receipt_credit_customer_credit_note(self):
        """Calculate receipt_credit_customer_credit_note based on conditions."""
        if self.move_type == "out_refund":
            if self.partner_id.receipt_credit:
                return str(self.partner_id.receipt_credit)
            elif len(self.credit_external_codes) > 1:
                if self.get_credit_payable_account_type() == "asset_receivable":
                    return str(self.credit_external_codes[1])
        return ""

    def get_custom_name(self):
        """Generate custom name based on conditions."""
        reference = (self.journal.ref or "").replace("\u2066", "").replace("\u2069", "")
        partner_name = self.partner_id.name or False
        return f"{self.journal.name} {reference} {partner_name}"

    def get_fields_as_dict(self):
        """Calculate all required fields and return as a dictionary."""
        result = {
            'name': self.name,
            'credit_account_code_1': self.get_credit_account_code_1(),
            'credit_account_code_2': self.get_credit_account_code_2(),
            'credit_account_code_3': self.get_credit_account_code_3(),
            'withholding_credit_account_code': self.get_withholding_credit_account_code(),
            'credit_amount_1': self.get_credit_amount_1(),
            'credit_amount_2': self.get_credit_amount_2(),
            'credit_amount_3': self.get_credit_amount_3(),
            'credit_amount_4': self.get_credit_amount_4(),
            'debit_amount_3': self.get_debit_amount_3(),
            'debit_amount_4': self.get_debit_amount_4(),
            'withholding_credit_amount': self.get_withholding_credit_amount(),
            'withholding_credit_amount_1': self.get_withholding_credit_amount_1(),
            'receipt_credit_journal_entry': self.get_receipt_credit_journal_entry(),
            'receipt_credit_vendor_bill': self.get_receipt_credit_vendor_bill(),
            'receipt_credit_customer_credit_note': self.get_receipt_credit_customer_credit_note(),
            'custom_name': self.get_custom_name(),
        }
        return result

    # NOW WE MOVE ON TO POST-DICT EXTERNAL CALCULATION METHODS, THAT ARE REQUIRED IN THE MAIN PROGRAM.

    def extcalc_credit_account1(self):
        """Get the final credit_account1 based on conditions."""
        if self.get_receipt_credit_journal_entry():
            return self.get_receipt_credit_journal_entry()
        if self.get_receipt_credit_vendor_bill():
            return self.get_receipt_credit_vendor_bill()
        if self.get_receipt_credit_customer_credit_note():
            return self.get_receipt_credit_customer_credit_note()
        if self.credit_external_software_code and int(self.credit_external_software_code) != 0:
            return self.credit_external_software_code
        return self.get_credit_account_code_1()

    def extcalc_credit_account2(self, amount_tax):
        """Get the final credit_account2 based on conditions."""
        if self.get_withholding_credit_account_code():
            return self.get_withholding_credit_account_code()
        if amount_tax != 0:
            if self.get_credit_account_code_2():
                return self.get_credit_account_code_2()
            if self.get_credit_account_code_3():
                return self.get_credit_account_code_3()
        return ""

    def extcalc_credit_amount_1(self, amount_tax):
        """Get the final credit_amount_1 based on conditions."""
        if self.get_withholding_credit_amount_1():
            return self.get_withholding_credit_amount_1()
        if self.get_credit_amount_3() and self.journal_tax_ids and amount_tax == 0:
            return self.get_credit_amount_3()
        return self.get_credit_amount_1()

    def extcalc_credit_amount_2(self, amount_tax):
        """Get the final credit_amount_2 based on conditions."""
        if self.get_withholding_credit_amount():
            return self.get_withholding_credit_amount()
        if amount_tax != 0 and self.get_credit_amount_2():
            return self.get_credit_amount_2()
        return ""
