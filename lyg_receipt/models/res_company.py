#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################
from odoo import models, api, fields, _
from odoo.exceptions import UserError
from datetime import datetime
from odoo.fields import Datetime, Date
from odoo.tools.misc import format_date
import pytz


class ResCompany(models.Model):
    _inherit = 'res.company'

    receipt_restrict_mode_hash = fields.Boolean(
        "Lock Posted Receipts with Hash", readonly=True)
    receipt_sequence_id = fields.Many2one('ir.sequence')
    send_an_email_receipts = fields.Boolean("Send a Receipt")

    def _create_secure_sequence_receipt(self, sequence_fields):
        """This function creates a no_gap sequence on each company in self that will ensure
        a unique number is given to all posted receipt.
        """
        for company in self:
            vals_write = {}
            for seq_field in sequence_fields:
                if not company[seq_field]:
                    vals = {
                        'name': _('Securisation of %s - %s') % (
                        seq_field, company.name),
                        'code': 'FRSECURE%s-%s' % (company.id, seq_field),
                        'implementation': 'no_gap',
                        'prefix': '',
                        'suffix': '',
                        'padding': 0,
                        'company_id': company.id}
                    seq = self.env['ir.sequence'].create(vals)
                    vals_write[seq_field] = seq.id
            if vals_write:
                company.write(vals_write)

    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)
        for company in companies:
            if company.receipt_restrict_mode_hash \
                    and not company.receipt_sequence_id:
                sequence_fields = ['receipt_sequence_id']
                company._create_secure_sequence(sequence_fields)
        return companies

    def write(self, vals):
        res = super(ResCompany, self).write(vals)
        for company in self:
            if company.receipt_restrict_mode_hash and \
                    not company.receipt_sequence_id:
                sequence_fields = ['receipt_sequence_id']
                company._create_secure_sequence_receipt(sequence_fields)
        return res
