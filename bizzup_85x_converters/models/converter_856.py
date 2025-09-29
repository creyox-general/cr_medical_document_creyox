# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

try:
    from currency_converter import CurrencyConverter
except ImportError:
    _logger.warning("currency_converter library not found. Please install it before use.")
    raise UserError("Missing Python library: currency_converter")


class Converter856(models.TransientModel):
    """
    Odoo-based "Converter 856" that fetches data directly from Odoo records
    (instead of reading from a .dat file) and turns them into a dict stream of the record
    """
    _name = 'converter.856'
    _description = 'Converts data from Odoo records to 856 reports (Odoo model)'

    # This method fetches the records based on vendor payments.
    def fetch_records_from_payments(self, start_date=None, end_date=None):
        # Step 1: Get all vendor payment records
        vendor_payments = self.env['account.payment'].search([
            ('partner_type', '=', 'supplier'),
            ("payment_type", "=", "outbound"),
            ("excluded_in_856_857_report", "=", False),
            ('company_id', '=', self.env.company.id),
            ("state", "in", ["paid", "in_process"]),
        ])

        _logger.info("Vendor payments collected list length: %s", len(vendor_payments))

        # Extract journal entries from these vendor payments
        payments_moves = vendor_payments.mapped('move_id')
        payments_move_id_search_array = [int(move.id) for move in payments_moves]

        _logger.info("Payment linked move IDs: %s", [int(move.id) for move in payments_moves])

        # Step 2: Get the relevant moves based on existing filtering mechanism
        moves_by_payment_ids = self.env['account.move'].search([
            ('id', 'in', payments_move_id_search_array),
            ('state', '=', 'posted'),
            ('company_id', '=', self.env.company.id),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
        ])

        # After this, if there's nothing to process, catch
        if not moves_by_payment_ids:
            raise UserError("No relevant payments or moves found for the current company.")

        _logger.info("ID field check: %s", [int(move.id) for move in moves_by_payment_ids])

        # Step 3: Filter by relevant IDs only
        moves_filtered_by_id = [
            move for move in moves_by_payment_ids
            if move.id in payments_move_id_search_array
        ]

        _logger.info("Moves filtered by ID: %s", moves_filtered_by_id)
        _logger.info("Post-ID filter length: %s", len(moves_filtered_by_id))

        # Step 4: Identify payment moves that contain account '111200'
        moves_with_account_111200 = [
            move for move in moves_filtered_by_id
            if '111200' in [line.account_id.code for line in move.line_ids]
        ]

        _logger.info("Account 111200 move collection length: %s", len(moves_with_account_111200))

        moves_without_account_111200 = [
            move for move in moves_filtered_by_id
            if '111200' not in [line.account_id.code for line in move.line_ids]
        ]

        _logger.info("Non-account-111200 move collection length: %s", len(moves_without_account_111200))

        # Step 5: Filter payment moves without account 111200 to include only those before April 2025
        filtered_moves_without_account = [
            move for move in moves_without_account_111200 if move.date < datetime.now().date().replace(year=2025, month=4, day=1)
        ]

        _logger.info("Filtered non-account-111200 move collection length: %s", len(filtered_moves_without_account))

        # Combine both lists to form the final move-by-payment list, and return
        moves_filtered_by_account = moves_with_account_111200 + filtered_moves_without_account

        _logger.info("Filtering result of payment method: %s\n\n", moves_filtered_by_account)

        return moves_filtered_by_account


    # This method handles all the cases that cannot be detected using the vendor payment method.
    def fetch_records_from_movements(self, start_date=None, end_date=None):
        # Step 1: Get the relevant moves according to the search conditions
        moves_unfiltered_by_account = self.env['account.move'].search([
            ("payment_state", "not in", ["not_paid", "blocked"]),
            ('state', '=', 'posted'),
            ('company_id.id', '=', self.env.company.id),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
        ])

        _logger.info("Unlinked legal move IDs: %s", [int(move.id) for move in moves_unfiltered_by_account])

        # Step 2: Map out only the moves in which the relevant account appears
        moves_filtered_by_account = [move for move in moves_unfiltered_by_account
                                     if '111200' in [line.account_id.code for line in move.line_ids]]  # Switch to 111200

        _logger.info("Filtering result of account-move method: %s\n\n", moves_filtered_by_account)

        return moves_filtered_by_account

    @api.model
    def convert_856(self,
                    start_date_filter=datetime.now().date().replace(month=1, day=1),
                    end_date_filter=datetime.now().date().replace(month=12, day=31)):
        """
        1. Fetch data from Odoo (filtering from account.move)
        2. Use currency_converter for any currency → ILS conversions
        3. Build r60, r70, r80 data structures
        4. Return a dictionary with the final results
        """

        # In contrast to the 857 converter, here we have a single function generator that relies on helpers.
        # For that reason, the databases are handled locally and not in the class scope.
        transactions_database = []
        company_data = {}  # Defined w/o extra calculations - still better to mention it here, good coding principles and all that
        vendor_database = {}
        r60_database = {}
        r70_record = {}  # Same as company_data
        r80_database = {}

        start_date = datetime.now().date().replace(month=1, day=1)
        end_date = datetime.now().date().replace(month=12, day=31)

        # Check for valid start and end dates, else assign default
        if start_date_filter:
            start_date = start_date_filter
        if end_date_filter:
            end_date = end_date_filter

        # Extract all relevant records from ODOO using both filtering methods available
        payment_moves = self.fetch_records_from_payments(start_date, end_date)
        other_moves = self.fetch_records_from_movements(start_date, end_date)

        # Combine and check for record status - If there's nothing to process, avoid creating a bug report
        combined_move_list = list(set(payment_moves + other_moves))

        if not combined_move_list:
            raise UserError("No relevant payments or moves found for the current company.")

        # Convert to Odoo recordset and use
        moves = self.env['account.move'].browse([move.id for move in combined_move_list])

        # If no moves found despite all that, throw an error.
        if not moves:
            raise UserError("Cannot find relevant moves in current ODOO DB.")

        # Set company data ahead of processing
        company = moves[0].company_id
        payer_status = '1' if company.partner_id.company_status == 'company' \
            else '2' if company.partner_id.company_status == 'single_person' \
            else '3' if company.partner_id.company_status == 'partnership' \
            else '4' if company.partner_id.company_status == 'ngo' \
            else '5' if company.partner_id.company_status == 'state_company' \
            else company.partner_id.company_status or ''

        company_data = {
            'withholding_tax_num': company.l10n_il_withh_tax_id_number,
            'report_const': '96',
            'tax_year_const': moves[0].date.strftime('%Y/%m').split('/')[0],
            'income_tax_num': company.vat,
            'payer_status': payer_status,
            'email': company.email,
            'phone': company.phone,
        }

        for move in moves:
            # Get vendor data as an object, then strip down in dictionary.
            partner = move.partner_id
            receiver_id = str(partner.id)  # dict identifier for vendor

            # Handle special fields accordingly.
            special_code = '2' if str(partner.code) == 'PS' \
                else '3' if str(partner.code) != 'IL' and str(partner.company_type) == 'person' \
                else '5' if str(partner.code) != 'IL' and str(partner.company_type) == 'company' \
                else ''
            business_code = '3' if str(partner.company_type) == 'company' and partner.company_registry \
                else '2' if str(partner.company_type) == 'company' \
                else '1' if str(partner.company_type) == 'person' \
                else ''

            # If the vendor is unrecognised, create vendor entry and initialise vendor details
            if receiver_id not in vendor_database:
                vendor_database[receiver_id] = {
                    "income_tax_num": partner.vat or '',
                    "special_code": special_code,
                    "business_code": business_code,
                    "name": partner.display_name or '',
                    "street": partner.street or '',
                    "city": partner.city or '',
                    "description": (",".join(tag.display_name for tag in partner.category_id))
                }

            # Get the timestamp from the move itself
            move_year = move.date.strftime('%Y/%m').split('/')[0]
            move_month = move.date.strftime('%Y/%m').split('/')[1]

            # Assign transaction amounts, and convert to ILS if needed
            currency = move.currency_id.name
            amount_total = self._convert_to_shekels_if_needed(
                round(move.amount_total, 2),
                currency)
            amount_tax = self._convert_to_shekels_if_needed(
                round(move.amount_tax, 2),
                currency)

            # Calculate the withholding amount (Current withholding module code is flawed, and not working, so I wrote something myself)
            lines_111200 = [line for line in move.line_ids if line.account_id.code == '111200']
            # Sum credit and debit amounts for account 111200
            total_credit_111200 = sum(line.credit for line in lines_111200)
            total_debit_111200 = sum(line.debit for line in lines_111200)
            withholding_amount_sum = total_credit_111200 - total_debit_111200
            # Format the field and assign
            amount_withhold = self._convert_to_shekels_if_needed(round(withholding_amount_sum or 0, 2), currency)

            # Calculating extra fields
            withhold_percent = str(partner.withholding_tax_rate)
            dividend_indicator = '1' if move.partner_id.withholding_tax_reason.code == '18' else '0'
            ta_branch_creds = ((move.partner_id.l10n_il_ita_branch.display_name or '')
                               + (move.partner_id.l10n_il_ita_branch.code or ''))
            withholding_reason = move.partner_id.withholding_tax_reason.code or ''

            # Add a new transaction to transactions_database
            transactions_database.append({
                "receiver_id": receiver_id,
                "tax_year": move_year,
                "tax_month": move_month,
                "currency": currency,
                "amount_total": amount_total,
                "amount_tax": amount_tax,
                "amount_withhold": amount_withhold or 0.0,
                "withhold_percent": withhold_percent or 0.0,
                "dividend_indicator": dividend_indicator,
                "ta_branch_creds": ta_branch_creds,
                "withholding_reason": withholding_reason,
            })

        # Start calculating r60 based on the raw data
        for transaction in transactions_database:
            receiver_id = transaction["receiver_id"]
            vendor = vendor_database[receiver_id]
            tax_year = transaction["tax_year"]
            wthld_percent = transaction["withhold_percent"]

            # If there's a mismatch in the move tax year vs. the registered company transaction year, issue an error
            if tax_year != company_data["tax_year_const"]:
                raise UserError(
                    "Tax year mismatch between the Company configuration (%s) and a transaction (%s)."
                    % (company_data["tax_year_const"], tax_year)
                )

            condition_string = f'recvid{receiver_id}wthld%{wthld_percent}'
            if condition_string not in r60_database:
                r60_database[condition_string] = {
                    "Company Withholding Tax Number": company_data["withholding_tax_num"],
                    "Report Code": company_data["report_const"],
                    "Tax Year": tax_year,
                    "Receiver Special Code": vendor["special_code"],
                    "Receiver Business Code": vendor["business_code"],
                    "Receiver Income Tax Number": vendor["income_tax_num"],
                    "Receiver System ID": receiver_id,
                    "Receiver Name": vendor["name"],
                    "Receiver Street Address": vendor["street"],
                    "Receiver City": vendor["city"],
                    "Total Amount Paid": round(transaction["amount_total"], 2),
                    "Taxed Amount": round(transaction["amount_tax"], 2),
                    "Withheld Amount": round(transaction["amount_withhold"], 2) or 0.0,
                    "Additional Fees": 0,
                    "Withholding Rate (%)": wthld_percent,
                    "TA Branch Name and Code": transaction["ta_branch_creds"],
                    "Vendor Business Description": vendor["description"],
                    "Withholding Reason": transaction["withholding_reason"],
                    "Record Type": 60
                }
            else:
                # Update the total transaction value for the vendor
                old_total = r60_database[condition_string]["Total Amount Paid"]
                old_taxed = r60_database[condition_string]["Taxed Amount"]
                old_withhold = r60_database[condition_string]["Withheld Amount"]
                r60_database[condition_string].update({
                    "Total Amount Paid": round(old_total + transaction["amount_total"], 2),
                    "Taxed Amount": round(old_taxed + transaction["amount_tax"], 2),
                    "Withheld Amount": round(old_withhold + transaction["amount_withhold"], 2) or 0.0
                })

        # Start calculating the r70 report based on the already calculated r60 DB
        total_foreign = 0
        tax_foreign = 0
        total_paid = 0
        total_tax = 0
        total_withheld = 0

        for r60 in r60_database.values():
            total_paid += r60["Total Amount Paid"]
            total_tax += r60["Taxed Amount"]
            total_withheld += r60["Withheld Amount"]
            # If the receiver special code is not empty then add the amounts to foreign payments
            if r60["Receiver Special Code"]:
                total_foreign += r60["Total Amount Paid"]
                tax_foreign += r60["Taxed Amount"]

        # Issue the r70 record as a dictionary
        r70_record = {
            "Company Withholding Tax Number": company_data["withholding_tax_num"],
            "Report Code": company_data["report_const"],
            "Tax Year": company_data["tax_year_const"],
            "Additional Report Indicator": ' ',
            "Company Payer Status Code": company_data["payer_status"],
            "Company Income Tax Number": company_data["income_tax_num"],
            "Payments Total Sum (Foreign Resident)": round(total_foreign, 2),
            "Total Tax Withheld (Foreign Resident)": round(tax_foreign, 2),
            "Additional Fees (Foreign Resident)": ' ',
            "Company Phone Number": company_data["phone"],
            "Total Amount Paid": round(total_paid, 2),
            "Withheld Amount": round(total_withheld, 2) or 0.0,
            "Taxed Amount": round(total_tax, 2),
            "Number of Recipients": len(vendor_database),
            "Number of Records": len(r60_database),
            "Company Email": company_data["email"],
            "Check Field": 'בדיקה',
            "Record Type": 70
        }

        # Initialise r80 database to default values, according to the ITA instructions
        for month in range(1, 13):
            if month < 10:
                month = "0" + str(month)
            r80_database[str(month)] = {
                "_vnd_list": [],
                "Company Withholding Tax Number": company_data["withholding_tax_num"],
                "Report Code": company_data["report_const"],
                "Tax Year": company_data["tax_year_const"],
                "Tax Month": month,
                "Number of Recipients": 0,
                "Non-Dividend Payments": 0,
                "Non-Dividend Withheld Tax": 0,
                "Dividend Payments": 0,
                "Dividend Withheld Tax": 0,
                "Total Tax Paid": 0,
                "Record Type": 80
            }

        # Start calculating r80 based on previous data
        for trx in transactions_database:
            month = trx["tax_month"]
            db = r80_database[month]
            db["_vnd_list"].append(trx["receiver_id"])
            db["Total Tax Paid"] = round(db["Total Tax Paid"] + trx["amount_tax"], 2)

            if trx["dividend_indicator"]:
                db["Dividend Payments"] = round(db["Dividend Payments"] + trx["amount_total"], 2)
                db["Dividend Withheld Tax"] = round(db["Dividend Withheld Tax"] + trx["amount_withhold"], 2)
            else:
                db["Non-Dividend Payments"] = round(db["Non-Dividend Payments"] + trx["amount_total"], 2)
                db["Non-Dividend Withheld Tax"] = round(db["Non-Dividend Withheld Tax"] + trx["amount_withhold"], 2)

        # finalise r80
        for record in r80_database.values():
            record["Number of Recipients"] = len(set(record["_vnd_list"]))
            del record["_vnd_list"]

        # Return r60, r70 and r80 as a unified 856 report (returned as a dict stream)
        unified_856_report = {
            "r60": r60_database,
            "r70": r70_record,
            "r80": r80_database,
        }

        # Print the final result the return
        _logger.info(unified_856_report)
        return unified_856_report

    # An internal foreign currency converter
    def _convert_to_shekels_if_needed(self, amount, from_currency):
        """
        A simple foreign-currency to ILS converter (in case of need)
        """
        if from_currency != 'ILS':
            return CurrencyConverter.convert(amount, from_currency, 'ILS')
        return amount
