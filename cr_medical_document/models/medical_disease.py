# -*- coding: utf-8 -*-
# Part of Creyox Technologies

from odoo import fields, models, api, _


class MedicalDisease(models.Model):
    _name = "medical.disease"
    _description = "Medical Disease"
    _rec_name = "procedure_name"

    medical_document_id = fields.Many2one('medical.record', string="Medical Document")
    procedure_name = fields.Char("Procedure Name")
    nomed_code = fields.Char("Nomed Code")
    code = fields.Char("Code")
    short_name = fields.Char("Short Name")
    long_name = fields.Char("Long Name")