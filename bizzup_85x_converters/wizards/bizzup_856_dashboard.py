# models/bizzup_856_dashboard.py
import base64
import json
import random
import logging
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError

from ..models.pdf_handler_856 import (
    create_r60_pdf, create_r70_pdf, create_r80_pdf
)
from ..models.txt_handler_856 import export_856_to_txt

_logger = logging.getLogger(__name__)

class Bizzup856Dashboard(models.TransientModel):
    _name = "bizzup.856.dashboard"
    _description = "856 Dashboard"

    # Initialise a start and end date. This will be the relevant transaction range.
    start_date = fields.Date(string="Start Date", default=datetime.now().date().replace(month=1, day=1))
    end_date = fields.Date(string="End Date", default=datetime.now().date().replace(month=12, day=31))

    # Store JSON from converter so we don't re-query:
    r60_data_json = fields.Text("R60 Data JSON", readonly=True)
    r70_data_json = fields.Text("R70 Data JSON", readonly=True)
    r80_data_json = fields.Text("R80 Data JSON", readonly=True)

    # Initialise a summary display for the 856 report
    r70_html = fields.Html("תצוגה כוללת - סיכום דו\"ח 856", sanitize=False)

    # Define the downloadable files as fields
    r60_pdf_binary = fields.Binary("R60 PDF", readonly=True, attachment=False)
    r60_pdf_name = fields.Char("R60 PDF Filename", readonly=True)

    r70_pdf_binary = fields.Binary("R70 PDF", readonly=True, attachment=False)
    r70_pdf_name = fields.Char("R70 PDF Filename", readonly=True)

    r80_pdf_binary = fields.Binary("R80 PDF", readonly=True, attachment=False)
    r80_pdf_name = fields.Char("R80 PDF Filename", readonly=True)

    report_856_txt_binary = fields.Binary("856 TXT", readonly=True, attachment=False)
    report_856_txt_name = fields.Char("856 TXT Filename", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        """Automatically reload data after creation."""
        records = super().create(vals_list)
        for record in records:
            # If both dates are set by default or provided in vals, call the reload:
            if record.start_date and record.end_date:
                record._reload_dashboard_data()
        return records

    # TODO: error issuing bug with overlapping dates - date reset not working
    @api.onchange('start_date', 'end_date')
    def _onchange_date_range(self):
        # If the user configured the dates in an invalid way, issue an error.
        if self.start_date and self.end_date and self.start_date > self.end_date:
            self.start_date = datetime.now().date().replace(month=1, day=1)
            self.end_date = datetime.now().date().replace(month=12, day=31)
            self.update({
                'start_date': fields.Date.today().replace(month=1, day=1),
                'end_date': fields.Date.today().replace(month=12, day=31),
            })
            return {
                'warning': {
                    'title': "Invalid Dates",
                    'message': "Start date cannot be after end date. Reverting to default dates.",
                }
            }
        if self.start_date and self.end_date and self.start_date.year != self.end_date.year:
            self.start_date = datetime.now().date().replace(month=1, day=1)
            self.end_date = datetime.now().date().replace(month=12, day=31)
            self.update({
                'start_date': fields.Date.today().replace(month=1, day=1),
                'end_date': fields.Date.today().replace(month=12, day=31),
            })
            return {
                'warning': {
                    'title': "Invalid Dates",
                    'message': "Start date and end date must be in the same year. Reverting to default dates.",
                }
            }

        # Reload the data to match the chosen dates.
        self._reload_dashboard_data()

    def action_reload_dashboard(self):
        self._reload_dashboard_data()

    def _reload_dashboard_data(self):
        """Fetch data from converter once, store JSON + build an HTML table for display."""
        self.r70_html = ""  # clear old lines

        # Get data from the converter856 class
        converter = self.env["converter.856"]
        try:
            report_database = converter.convert_856(
                start_date_filter=self.start_date,
                end_date_filter=self.end_date
            )
        except Exception as e:
            _logger.exception("Error processing 856 data.")
            raise UserError(f"Failed to process the 856 raw data. Error: {e}")

        # Store data for reuse in exports
        self.r60_data_json = json.dumps(report_database["r60"])
        self.r70_data_json = json.dumps(report_database["r70"])
        self.r80_data_json = json.dumps(report_database["r80"])

        # Build an HTML table from the fetched R70 data:
        r70_struct = report_database["r70"]
        rows = []

        # Turn the rows variable into a report divided by sections
        # "Company details"
        rows.append({
            "section": "פרטי החברה",
            "cols": [
                ("ח.פ", str(r70_struct.get("Company Withholding Tax Number"))),
                ("סטטוס משלם", str(r70_struct.get("Company Payer Status Code"))),
                ("תיק מס הכנסה", str(r70_struct.get("Company Income Tax Number"))),
                ("טלפון חברה", str(r70_struct.get("Company Phone Number"))),
                ("דוא\"ל חברה", str(r70_struct.get("Company Email"))),
            ],
        })

        # "Additional Report Info"
        rows.append({
            "section": "פרטים נוספים על הדו\"ח",
            "cols": [
                ("קוד דיווח", str(r70_struct.get("Report Code"))),
                ("שנת מס", str(r70_struct.get("Tax Year"))),
                ("דו\"ח נוסף?", str(r70_struct.get("Additional Report Indicator"))),
            ],
        })

        # "Foreign Resident Payments"
        rows.append({
            "section": "תשלומים לתושבי חוץ",
            "cols": [
                ("סה\"כ תשלומים", str(r70_struct.get("Payments Total Sum (Foreign Resident)"))),
                ("ניכוי מס", str(r70_struct.get("Total Tax Withheld (Foreign Resident)"))),
                ("עמלות נוספות", str(r70_struct.get("Additional Fees (Foreign Resident)"))),
            ],
        })

        # "Payments Summary"
        rows.append({
            "section": "סיכום תשלומים",
            "cols": [
                ("סה\"כ תשלומים", str(r70_struct.get("Total Amount Paid"))),
                ("ניכוי מס", str(r70_struct.get("Withheld Amount"))),
                ("מע\"מ/מיסוי", str(r70_struct.get("Taxed Amount"))),
            ],
        })

        # "Additional Info About the Recipients"
        rows.append({
            "section": "מידע על המקבלים",
            "cols": [
                ("מספר מקבלים", str(r70_struct.get("Number of Recipients"))),
                ("מספר רשומות", str(r70_struct.get("Number of Records"))),
            ],
        })

        # Convert these row dicts to HTML display
        html_content = self._build_html_table(rows)
        self.r70_html = html_content

        # Reset all downloadable fields so we can reload new data
        self.r60_pdf_binary = False
        self.r60_pdf_name = False
        self.r70_pdf_binary = False
        self.r70_pdf_name = False
        self.r80_pdf_binary = False
        self.r80_pdf_name = False
        self.report_856_txt_binary = False
        self.report_856_txt_name = False


    def _build_html_table(self, row_structs):
        """
        Build an HTML table from the row_structs list of dicts,
        Then uses it as a preview display for report 856.
        """
        table = [
            "<div style='border:1px solid #ccc; padding:10px;'>",
            "<table class='table table-condensed' style='width:100%;'>",
        ]
        # For each “section”, there will be a gray header for the section, then the sub-values
        for row_block in row_structs:
            table.append(f"<tr style='background-color:#eee; font-weight:bold;'><td colspan='2'>{row_block['section']}</td></tr>")
            for label, val in row_block['cols']:
                val_str = val if val not in (False, None) else ""
                table.append(f"<tr><td style='width:40%;'>{label}</td><td style='width:60%;'>{val_str}</td></tr>")

        # Finalise the table and return it as HTML code
        table.append("</table>")
        table.append("</div>")
        return "".join(table)

    # Export and download action for an R60 PDF
    def action_download_r60(self):
        # Build PDF
        r60_data = json.loads(self.r60_data_json)
        pdf_bytes = create_r60_pdf(r60_data)
        self.r60_pdf_binary = base64.b64encode(pdf_bytes)
        self.r60_pdf_name = "r60_report.pdf"

        # Return the URL, telling Odoo to download from the Binary field
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content?model=bizzup.856.dashboard'
                   f'&id={self.id}'
                   f'&field=r60_pdf_binary'
                   f'&filename_field=r60_pdf_name'
                   f'&download=true',
            'target': 'self',
        }

    # Export and download action for an R70 PDF
    def action_download_r70(self):
        # Build PDF
        r70_data = json.loads(self.r70_data_json)

        # >>> ADDED: include the selected period in the payload <<<
        start = fields.Date.to_date(self.start_date)
        end = fields.Date.to_date(self.end_date)
        r70_data["_report_period"] = {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "period_text": f"{start.strftime('%d/%m/%Y')} – {end.strftime('%d/%m/%Y')}",
        }
        # <<< END ADDITION >>>

        pdf_bytes = create_r70_pdf(r70_data)
        self.r70_pdf_binary = base64.b64encode(pdf_bytes)
        self.r70_pdf_name = "r70_report.pdf"

        # Return the URL, telling Odoo to download from the Binary field
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content?model=bizzup.856.dashboard'
                   f'&id={self.id}'
                   f'&field=r70_pdf_binary'
                   f'&filename_field=r70_pdf_name'
                   f'&download=true',
            'target': 'self',
        }

    # Export and download action for an R80 PDF
    def action_download_r80(self):
        # Build PDF
        r80_data = json.loads(self.r80_data_json)
        pdf_bytes = create_r80_pdf(r80_data)
        self.r80_pdf_binary = base64.b64encode(pdf_bytes)
        self.r80_pdf_name = "r80_report.pdf"

        # Return the URL, telling Odoo to download from the Binary field
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content?model=bizzup.856.dashboard'
                   f'&id={self.id}'
                   f'&field=r80_pdf_binary'
                   f'&filename_field=r80_pdf_name'
                   f'&download=true',
            'target': 'self',
        }

    # Export and download action for the txt file of the report itself
    def action_download_856_txt(self):
        # Fetch all data from the JSON fields
        r60_data = json.loads(self.r60_data_json)
        r70_data = json.loads(self.r70_data_json)
        r80_data = json.loads(self.r80_data_json)

        # Get the data in the structure of the file, then encode and turn to a bytestream
        txt_content_bytes = export_856_to_txt(r60_data, r70_data, r80_data)
        if isinstance(txt_content_bytes, str):
            txt_content_bytes = txt_content_bytes.encode('windows-1255', errors='replace')
        self.report_856_txt_binary = base64.b64encode(txt_content_bytes)

        # Construct the names of the file according to the instructions of the ITA
        eight_digit_id = str(random.randrange(10000000, 99999999))
        year_suffix = str(self.start_date.year)[1:]
        self.report_856_txt_name = f'A856.{eight_digit_id}.{year_suffix}'

        # Return the URL, telling Odoo to download from the Binary field
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content?model=bizzup.856.dashboard'
                   f'&id={self.id}'
                   f'&field=report_856_txt_binary'
                   f'&filename_field=report_856_txt_name'
                   f'&download=true',
            'target': 'self',
        }

    # We call this action whenever there is a refresh (date changing etc.)
    def _refresh_view(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current'
        }
