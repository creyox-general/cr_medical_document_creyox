import base64
import logging
import json
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from ..models.pdf_handler_856 import create_r60_pdf, create_r70_pdf, create_r80_pdf


_logger = logging.getLogger(__name__)


class Bizzup856Wizard(models.TransientModel):
    _name = "bizzup.856.wizard"
    _description = "Wizard to upload and convert raw system data into 856 reports"

    file_data = fields.Binary(string="Upload SIXIN .dat File", attachment=False)
    file_name = fields.Char(string="File Name")

    # R60: a single PDF report that includes merged vendor records
    r60_output_pdf = fields.Binary("R60 PDF", readonly=True, attachment=False)
    r60_output_name = fields.Char("R60 Filename", readonly=True)

    # R70: a single PDF report
    r70_output_pdf = fields.Binary("R70 PDF", readonly=True, attachment=False)
    r70_output_name = fields.Char("R70 Filename", readonly=True)

    # R80: a single PDF file that includes merged monthly reports
    r80_output_pdf = fields.Binary("R80 PDF", readonly=True, attachment=False)
    r80_output_name = fields.Char("R80 Filename", readonly=True)

    # Wizard state: before conversion, output is hidden
    state = fields.Selection(
        [('choose', 'Choose'), ('converted', 'Converted')],
        default='choose', string="Wizard State"
    )

    def action_process_file(self):
        """
        1) Decode the uploaded file.
        2) Parse with Converter856.
        3) For each record in converter, generate a separate PDF.
        4) Issue a one-time download link for each report, then display.
        """
        # self.ensure_one()
        # if not self.file_data:
        #     raise UserError(_("Please upload a .dat file first."))
        #
        # # Decode base64
        # try:
        #     file_bytes = base64.b64decode(self.file_data)
        # except Exception:
        #     _logger.exception("Error decoding base64 file data")
        #     raise UserError(_("Invalid file encoding."))
        #
        # # Attempt to decode with UTF-8 signed, fallback to replace errors
        # try:
        #     file_str = file_bytes.decode('utf-8-sig')
        # except UnicodeDecodeError:
        #     file_str = file_bytes.decode('utf-8-sig', errors='replace')
        #
        # # Parse with the converter class
        # converter = Converter856()
        # try:
        #     converter.read_file_content(file_str)
        #     converter.run_all_calculations()
        # except Exception as e:
        #     _logger.exception("Error processing 856 .dat file.")
        #     raise UserError(_("Failed to parse the .dat file. Error: %s") % str(e))

        converter856 = self.env['converter.856']
        try:
            report_database = converter856.convert_856()
            r60_database = report_database['r60']
            r70_record = report_database['r70']
            r80_database = report_database['r80']
        except Exception as e:
            _logger.exception("Error processing 856 data.")
            raise UserError(_("Failed to process the 856 raw data. Error: %s") % str(e))

        # Generate the singular R60 PDF from converter.r60_database
        pdf_bytes_r60 = create_r60_pdf(r60_database)
        self.r60_output_pdf = base64.b64encode(pdf_bytes_r60)
        self.r60_output_name = "r60_report.pdf"

        # Generate the singular R70 PDF from converter.r70_record
        pdf_bytes_r70 = create_r70_pdf(r70_record)
        self.r70_output_pdf = base64.b64encode(pdf_bytes_r70)
        self.r70_output_name = "r70_report.pdf"

        # Generate the singular R80 PDF from converter.r80_database (merging monthly reports)
        pdf_bytes_r80 = create_r80_pdf(r80_database)
        self.r80_output_pdf = base64.b64encode(pdf_bytes_r80)
        self.r80_output_name = "r80_report.pdf"

        # Change state so that output fields become visible
        self.state = 'converted'

        # Return the same wizard form to show lines
        return {
            'name': _("856 Conversion Wizard"),
            'type': 'ir.actions.act_window',
            'res_model': 'bizzup.856.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
