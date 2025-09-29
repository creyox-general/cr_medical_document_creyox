from odoo.addons.bizzup_movein_report.models.calc_helper import CalcHelper
import logging

_logger = logging.getLogger(__name__)

class DebitCalcHelper(CalcHelper):
    def __init__(self, journal):
        super().__init__(journal)

        # Initialize own filtered fields
        self._initialize_fields()

        _logger.info(f"DEBIT ROW NEWLY INITIALIZED NAME AS: {self.name}")

    def _initialize_fields(self):
        """Initialize and cache necessary fields for calculations."""
        # Filter tax IDs
        self.journal_tax_ids = self.journal.invoice_line_ids.filtered(
            lambda line: line.tax_ids and (tax.amount == 0 for tax in line.tax_ids))

        # Filter debit accounts
        self.journal_debit_accounts = self.journal.line_ids.filtered(lambda line: line.debit > 0)

        # Ensure self.journal_debit_accounts is an Odoo recordset
        if not self.journal_debit_accounts:
            self.journal_debit_accounts = self.journal.line_ids.browse([])  # Empty recordset

        # Filter VAT accounts within debit accounts
        self.journal_debit_vat_accounts = self.journal_debit_accounts.filtered(
            lambda line: str(line.account_id.code).startswith('111') or ""
        )

        # Map required fields
        self.debit_account_codes = self.journal_debit_accounts.mapped("account_id.code") or []
        self.debit_account_types = self.journal_debit_accounts.mapped("account_id.account_type") or []
        self.debit_external_codes = self.journal_debit_accounts.mapped("account_id.external_software_code") or []
        self.debit_vat_account_codes = self.journal_debit_vat_accounts.mapped("account_id.code") or []
        self.debit_amounts = self.journal_debit_accounts.mapped("debit") or []
        self.debit_vat_amounts = self.journal_debit_vat_accounts.mapped("debit") or []
        self.debit_external_software_code = self.debit_external_codes[0] or ""

    def is_debit_helper_valid(self):
        """Helper method to check account validity in journal."""
        return True if self.journal_debit_accounts else False

    def get_debit_receivable_account_type(self):
        """Get the receivable account type from debit accounts."""
        if self.debit_account_types:
            return self.debit_account_types[1] if len(self.debit_account_types) > 1 else self.debit_account_types[0]
        return ""

    def get_debit_non_receivable_account_type(self):
        """Get the non-receivable account type from debit accounts."""
        return self.debit_account_types[0] if self.debit_account_types else ""

    def get_debit_non_receivable_account_code(self):
        """Get the non-receivable account code from debit accounts."""
        if self.get_debit_non_receivable_account_type() != "asset_receivable":
            if self.debit_external_codes and self.debit_external_codes[0] > 0:
                return str(self.debit_external_codes[0])
        return ""

    def get_external_code_debit(self):
        """Get the external code for debit accounts."""
        return str(self.debit_external_codes[1]) if len(self.debit_external_codes) == 2 else ""

    def get_debit_account_code_1(self):
        """Calculate debit_account_code_1 based on conditions."""
        if self.debit_account_codes:
            if len(self.debit_account_codes) == 2:
                if self.move_type == "out_refund" and self.sale_order_count == 0 and self.debit_vat_account_codes:
                    vat_code = self.debit_vat_account_codes[0]
                    if vat_code in self.debit_account_codes:
                        index = self.debit_account_codes.index(vat_code)
                        other_index = 1 - index
                        return str(self.debit_account_codes[other_index])
                elif self.move_type == "in_refund":
                    return str(self.debit_account_codes[1])
                elif self.move_type == "out_invoice" and self.get_debit_receivable_account_type() == "asset_receivable":
                    return str(self.debit_account_codes[1])
            return str(self.debit_account_codes[0])
        return ""

    def get_debit_account_code_2(self):
        """Calculate debit_account_code_2 based on conditions."""
        if self.debit_external_codes and str(self.debit_external_codes[0]) != '0':
            return str(self.debit_external_codes[0])
        elif self.debit_vat_account_codes:
            return str(self.debit_vat_account_codes[0])
        elif len(self.debit_account_codes) > 1:
            non_receivable_code = self.get_debit_non_receivable_account_code()
            return non_receivable_code if non_receivable_code else str(self.debit_account_codes[1])
        return ""

    def get_debit_account_code_3(self):
        """Calculate debit_account_code_3 based on conditions."""
        _logger.info(f"DEBUG: debit_account_codes = {self.debit_account_codes}, debit_amounts = {self.debit_amounts}")
        if len(self.debit_amounts) == 2:
            if self.get_debit_non_receivable_account_type() != "asset_receivable" and self.move_type == "out_invoice":
                return str(self.debit_account_codes[0]) if len(self.debit_account_codes) > 0 else ""
            else:
                return str(self.debit_account_codes[1]) if len(self.debit_account_codes) > 1 else ""
        elif self.get_external_code_debit() != "0":
            return self.get_external_code_debit()
        elif self.move_type == "in_refund" and len(self.debit_account_codes) == 2 and self.amount_tax != 0:
            return str(self.debit_account_codes[0])
        return ""

    def get_withholding_debit_account_code(self):
        """Calculate withholding_debit_account_code based on conditions."""
        if self.move_type == "entry" and self.is_withholding and len(self.debit_account_codes) > 1:
            return str(self.debit_account_codes[1])
        return ""

    def get_debit_amount_1(self):
        """Calculate debit_amount_1 based on conditions."""
        amounts = self.debit_amounts
        amount = 0
        if len(amounts) >= 2:
            if len(amounts) == 4 and self.debit_vat_amounts:
                if self.move_type == "in_invoice" and self.purchase_order_count == 0:
                    amount = sum(amounts[:2]) + amounts[-1]
                elif self.move_type == "out_refund":
                    amount = sum(amounts[1:]) if self.payment_state == "paid" else sum(amounts[:-1])
            elif len(amounts) > 2 and self.debit_vat_amounts:
                amount = sum(amounts[:-1])
            elif self.move_type == "entry":
                amount = sum(amounts)
            elif self.move_type == "out_refund" and self.sale_order_count == 0 and self.amount_tax != 0:
                debit_code_1 = self.get_debit_account_code_1()
                if self.debit_account_codes[0] == debit_code_1:
                    amount = amounts[0]
                elif self.debit_account_codes[1] == debit_code_1:
                    amount = amounts[1]
            elif self.move_type == "in_refund" and self.amount_tax != 0:
                amount = amounts[1]
            elif self.get_debit_receivable_account_type() == "asset_receivable":
                amount = amounts[1]
                if self.move_type == "out_invoice":
                    amount = amounts[-1]
            elif self.amount_tax == 0:
                if self.move_type == "in_refund" and self.get_debit_non_receivable_account_type() != "asset_receivable":
                    amount = amounts[1]
                else:
                    amount = amounts[0]
            elif len(amounts) > 2 and len(self.debit_account_codes) >= 2:
                amount = self.amount_total
            else:
                amount = sum(amounts[:-1]) if len(amounts) > 2 else amounts[0]
        else:
            amount = sum(amounts)
        return "{:.2f}".format(amount).replace(".", "")

    def get_debit_amount_2(self):
        """Calculate debit_amount_2 based on conditions."""
        amount = 0
        if self.debit_vat_amounts:
            amount = self.debit_vat_amounts[0]
        elif self.get_debit_account_code_2():
            amount = self.get_debit_non_receivable_amount()
        elif len(self.debit_amounts) >= 2:
            if self.get_debit_non_receivable_account_type() != "asset_receivable" and self.move_type == "out_invoice":
                amount = self.debit_amounts[0]
            elif self.move_type == "in_refund" and self.amount_tax != 0:
                amount = self.debit_amounts[0]
            else:
                amount = self.debit_amounts[1]
        elif len(self.debit_amounts) > 2 and len(self.debit_account_codes) >= 2:
            amount = sum(self.debit_amounts[1:])
        return "{:.2f}".format(amount).replace(".", "")

    def get_debit_non_receivable_amount(self):
        """Get the amount for non-receivable accounts."""
        return self.debit_amounts[
            0] if self.get_debit_non_receivable_account_type() != "asset_receivable" and self.debit_amounts else 0

    def get_receipt_debit_journal_entry(self):
        """Calculate receipt_debit_journal_entry based on conditions."""
        if self.payment_id and self.payment_id.payment_type == "outbound" and self.partner_id.receipt_debit:
            return str(self.partner_id.receipt_debit)
        return ""

    def get_receipt_debit_customer_invoice(self):
        """Calculate receipt_debit_customer_invoice based on conditions."""
        if self.move_type == "out_invoice":
            if self.partner_id.receipt_debit:
                return str(self.partner_id.receipt_debit)
            elif len(self.debit_external_codes) > 1 and self.debit_external_codes[
                1] and self.get_debit_receivable_account_type() == "asset_receivable":
                return str(self.debit_external_codes[1])
        return ""

    def get_receipt_debit_vendor_credit_note(self):
        """Calculate receipt_debit_vendor_credit_note based on conditions."""
        if self.move_type == "in_refund":
            if self.partner_id.receipt_debit:
                return str(self.partner_id.receipt_debit)
            elif len(self.debit_external_codes) > 1 and self.debit_external_codes[
                1] and self.get_debit_receivable_account_type() == "liability_payable":
                return str(self.debit_external_codes[1])
        return ""

    def get_withholding_debit_amount(self):
        """Calculate withholding_debit_amount based on conditions."""
        if self.move_type == "entry" and self.is_withholding and len(self.debit_account_codes) > 1 and len(
                self.debit_amounts) > 1:
            amount = self.debit_amounts[1]
            return "{:.2f}".format(amount).replace(".", "")
        return ""

    def get_withholding_debit_amount_1(self):
        """Calculate withholding_debit_amount_1 based on conditions."""
        if self.move_type == "entry" and self.is_withholding:
            if self.payment_id and self.payment_id.receipt_id and self.payment_id.receipt_id.is_credit_receipt and len(
                    self.debit_account_codes) > 1 and len(self.debit_amounts) > 1:
                amount = sum(self.debit_amounts)
            else:
                amount = self.debit_amounts[0] if self.debit_amounts else 0
            return "{:.2f}".format(amount).replace(".", "")
        return ""

    def get_fields_as_dict(self):
        """Calculate all required fields and return as a dictionary."""
        result = {
            'name': self.name,
            'debit_account_code_1': self.get_debit_account_code_1(),
            'debit_account_code_2': self.get_debit_account_code_2(),
            'debit_account_code_3': self.get_debit_account_code_3(),
            'withholding_debit_account_code': self.get_withholding_debit_account_code(),
            'debit_amount_1': self.get_debit_amount_1(),
            'debit_amount_2': self.get_debit_amount_2(),
            'receipt_debit_journal_entry': self.get_receipt_debit_journal_entry(),
            'receipt_debit_customer_invoice': self.get_receipt_debit_customer_invoice(),
            'receipt_debit_vendor_credit_note': self.get_receipt_debit_vendor_credit_note(),
            'withholding_debit_amount': self.get_withholding_debit_amount(),
            'withholding_debit_amount_1': self.get_withholding_debit_amount_1(),
        }
        return result

    # NOW WE MOVE ON TO POST-DICT EXTERNAL CALCULATION METHODS, THAT ARE REQUIRED IN THE MAIN PROGRAM.

    def extcalc_debit_account1(self):
        """Get the final debit_account1 based on conditions."""
        if self.get_receipt_debit_journal_entry():
            return self.get_receipt_debit_journal_entry()
        if self.get_receipt_debit_customer_invoice():
            return self.get_receipt_debit_customer_invoice()
        if self.get_receipt_debit_vendor_credit_note():
            return self.get_receipt_debit_vendor_credit_note()
        if self.debit_external_software_code and int(self.debit_external_software_code) != 0:
            return self.debit_external_software_code
        return self.get_debit_account_code_1() or ""

    def extcalc_debit_account2(self, amount_tax):
        """Get the final debit_account2 based on conditions."""
        if self.get_withholding_debit_account_code():
            return self.get_withholding_debit_account_code()
        if amount_tax != 0:
            if self.get_debit_account_code_2():
                return self.get_debit_account_code_2()
            if self.get_debit_account_code_3():
                return self.get_debit_account_code_3()
        return ""

    def extcalc_debit_amount_1(self, amount_tax, debit_amount3, debit_amount4):
        """Get the final debit_amount_1 based on conditions."""
        if self.get_withholding_debit_amount_1():
            return self.get_withholding_debit_amount_1()
        if (debit_amount4 or debit_amount3) and self.journal_tax_ids and amount_tax == 0:
            return debit_amount4 or debit_amount3
        return self.get_debit_amount_1()

    def extcalc_debit_amount_2(self, amount_tax):
        """Get the final debit_amount_2 based on conditions."""
        if self.get_withholding_debit_amount():
            return self.get_withholding_debit_amount()
        if amount_tax != 0 and self.get_debit_amount_2():
            return self.get_debit_amount_2()
        return ""
