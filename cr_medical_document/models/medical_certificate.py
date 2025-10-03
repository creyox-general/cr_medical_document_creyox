# -*- coding: utf-8 -*-
# Part of Creyox Technologies

from odoo import fields, models, api, _


class MedicalCertificate(models.Model):
    _name = "medical.certificate"
    _description = "Medical Certificate"

    name = fields.Char(string="Certificates")
    sequence = fields.Integer("Sequence", default=1)
    expiration_date = fields.Datetime(string="Expiration Date")
    certificate_file = fields.Binary("Certificate File")
    certificate_filename = fields.Char("Certificate Filename")
    employee_id = fields.Many2one('hr.employee', string="Employee")