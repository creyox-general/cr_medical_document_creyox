from odoo import models, fields, _, api, Command

import logging
_logger = logging.getLogger(__name__)

class OiiInvoiceDetailsWizard(models.TransientModel):
    _name = 'oii.invoice.details.wizard'
    _description = "Document Details Wizard"

    invoice_type = fields.Integer(string="Invoice Type")
    vat_number = fields.Char(string="Vat Number")
    reference_number = fields.Char(string="Reference Number")
    customer_vat_number = fields.Char(string="Customer Vat Number")
    customer_name = fields.Char(string="Customer Name")
    invoice_date = fields.Date(string="Invoice Date")
    invoice_issuance_date = fields.Date(string="Invoice Issuance Date")
    amount_untaxed = fields.Float(string="Amount Untaxed")
    amount_tax = fields.Float(string="Amount Tax")
    amount_total = fields.Float(string="Amount Total")
