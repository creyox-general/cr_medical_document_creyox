import base64
import logging
import json
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from ..models.report_handler_857 import create_857_pdf


_logger = logging.getLogger(__name__)


class Bizzup857Wizard(models.TransientModel):
    _name = "bizzup.857.wizard"
    _description = "Wizard to upload and convert raw system data into 857 reports"

    file_data = fields.Binary(string="Upload EFCIN .dat File", attachment=False)
    file_name = fields.Char(string="File Name")

    # For demonstration, we produce a downloadable JSON file of the report_database
    output_data = fields.Binary("857 Report Data", readonly=True, attachment=False)
    output_filename = fields.Char("Output Filename", readonly=True)

    # Wizard state: before conversion, output is hidden
    state = fields.Selection(
        [('choose', 'Choose'), ('converted', 'Converted')],
        default='choose', string="Wizard State"
    )

    def action_process_file(self):
        """
        Process the uploaded 857 .dat file:
          1) Decode the file.
          2) Instantiate Converter857 with the file content.
          3) Run conversion to produce the 857 report_database.
          4) Store the JSON result in output_data for download.
        """
        # self.ensure_one()
        # if not self.file_data:
        #     raise UserError(_("Please upload a .dat file first."))
        #
        # try:
        #     file_bytes = base64.b64decode(self.file_data)
        # except Exception:
        #     _logger.exception("Error decoding base64 file data")
        #     raise UserError(_("Invalid file encoding."))
        #
        # try:
        #     file_str = file_bytes.decode('utf-8-sig')
        # except UnicodeDecodeError:
        #     file_str = file_bytes.decode('utf-8-sig', errors='replace')

        # Run the 857 converter
        converter857 = self.env['converter.857']
        try:
            report_database = converter857.convert_857()
        except Exception as e:
            _logger.exception("Error processing 857 data.")
            raise UserError(_("Failed to process the 857 raw data. Error: %s") % str(e))

        # Convert the report_database a formatted PDF stream
        pdf_bytes_857 = create_857_pdf(report_database)
        self.output_data = base64.b64encode(pdf_bytes_857)
        self.output_filename = "857_report.pdf"

        # Change state so that output fields become visible
        self.state = 'converted'

        return {
            'name': _("857 Conversion Wizard"),
            'type': 'ir.actions.act_window',
            'res_model': 'bizzup.857.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
