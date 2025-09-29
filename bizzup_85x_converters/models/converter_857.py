from odoo import models, fields, api, _
from odoo.addons.sale_stock.models.res_company import company
from odoo.exceptions import UserError
import logging
from currency_converter import CurrencyConverter

_logger = logging.getLogger(__name__)

class Converter857(models.Model):
    """
    Odoo-based "Converter 857" that fetches data directly from Odoo records
    (instead of reading from a .dat file) and turns them into a dict stream of the record
    """
    _name = 'converter.857'
    _description = 'Generates 857 report raw data'

    # Initialise year start and end as date range
    date_start = fields.Date.today().replace(month=1, day=1)
    date_end = fields.Date.today().replace(month=12, day=31)

    # This is a class-wide database. Whenever we'll refer to it,
    # we'll use "Converter857..." instead of "self".
    transaction_database = {}
    report_database = []
    company_data = {}

    # Read data similar to the hashavshevet module
    def read_moves(self):
        """
        Fetch moves from ODOO database according to the conditions specified
        in the base configuration.
        """

        # Get the relevant moves according to the search conditions
        moves = self.env['account.move'].search([
            ("company_id", "=?", self.env.company.id),
            ("date", ">=", self.date_start),
            ("date", "<=", self.date_end),
            ('state', '=', 'posted'),
            ('move_type', '=', 'in_invoice')
        ])

        if not moves:
            raise UserError(_("No posted moves found for the current company."))

        # Set company data ahead of processing
        Converter857.company_data = {
            "company_name": moves[0].company_id.name,
            "company_address": moves[0].company_id.partner_id.contact_address or '',
            "company_withhold_tax_number": (
                moves[0].company_id.vat or moves[0].company_id.company_registry or ''
            ),
        }

        for move in moves:
            # This is the move's vendor. We're fetching his data.
            vendor = move.partner_id
            vendor_name = vendor.name or ' '
            vendor_address = vendor.contact_address or ' '
            vendor_income_tax_number = vendor.vat or ' '

            # In case of need, do a currency exchange
            currency = move.currency_id.name
            total_amount = self._convert_to_shekels_if_needed(move.amount_total, currency)

            # Define the economical (transaction fields)
            additional_amount = 0.0
            vat_amount = 0.0
            for line in move.line_ids.filtered(lambda l: l.tax_line_id):
                vat_amount += line.price_total

            # Define the report date (according to format)
            date_month = move.date.month
            date_year = move.date.year % 100  # Two-digit year

            # Initialize vendor entry if not defined yet
            if vendor_name not in Converter857.transaction_database:
                Converter857.transaction_database[vendor_name] = {
                    'vendor_transactions': [],
                    'vendor_details': {
                        "vendor_name": vendor_name,
                        "vendor_address": vendor_address,
                        "vendor_income_tax_number": vendor_income_tax_number
                    }
                }

            # Add transaction to vendor so we can later summarise it
            Converter857.transaction_database[vendor_name]['vendor_transactions'].append({
                "transaction_date_month": str(date_month).zfill(2),
                "transaction_date_year": str(date_year).zfill(2),
                "total_amount": round(total_amount, 2),
                "additional_amount": round(additional_amount, 2),
                "vat_amount": round(vat_amount, 2)
            })

    # An internal foreign currency converter
    def _convert_to_shekels_if_needed(self, amount, from_currency):
        """
        A simple foreign-currency to ILS converter (in case of need)
        """
        if from_currency != 'ILS':
            return CurrencyConverter.convert(amount, from_currency, 'ILS')
        return amount


    def do_857_conversion(self):
        """
        Convert the transactions to build the 857-style report database.
        """
        from datetime import datetime
        current_year = str(datetime.now().year)[-2:]

        # Merge the transactions into a summary dict line
        for vendor_name, vendor_data in Converter857.transaction_database.items():
            report_total_amount = 0
            report_additional_amount = 0
            report_vat_amount = 0
            report_raw_months = [0] * 12
            report_months = {}

            for transaction in vendor_data['vendor_transactions']:
                if transaction['transaction_date_year'] == current_year:
                    month_idx = int(transaction['transaction_date_month']) - 1
                    report_raw_months[month_idx] = 1
                    report_total_amount += transaction['total_amount']
                    report_additional_amount += transaction['additional_amount']
                    report_vat_amount += transaction['vat_amount']

            for i in range(12):
                report_months[str(i+1)] = 'X' if report_raw_months[i] else ' '

            # Add a vendor report to the 857 report DB
            Converter857.report_database.append({
                "company_name": Converter857.company_data.get('company_name', ''),
                "company_address": Converter857.company_data.get('company_address', ''),
                "company_withhold_tax_number": Converter857.company_data.get('company_withhold_tax_number', ''),
                "vendor_name": vendor_name,
                "vendor_address": vendor_data['vendor_details'].get('vendor_address', ''),
                "vendor_income_tax_number": vendor_data['vendor_details'].get('vendor_income_tax_number', ''),
                "report_year": datetime.now().year,
                "report_months": report_months,
                "report_total_amount": round(report_total_amount, 2),
                "report_additional_amount": round(report_additional_amount, 2),
                "report_vat_amount": round(report_vat_amount, 2)
            })


    def convert_857(self):
        """
        Public method called by Odoo to trigger the read+convert process.
        """

        # Clear out old data
        Converter857.transaction_database = {}
        Converter857.report_database = []
        Converter857.company_data = {}

        # Initiate conversion`
        self.read_moves()
        self.do_857_conversion()
        return Converter857.report_database
