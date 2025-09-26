# -*- coding: utf-8 -*-
# Part of Creyox Technologies

from odoo import fields, models, api, _


class MedicalVitals(models.Model):
    _name = "medical.vitals"
    _description = "Medical Vitals"

    medical_document_id = fields.Many2one('medical.record', string="Medical Document")
    item = fields.Char("Item")
    value = fields.Float("Value")
    unit = fields.Char(string="Units")
    valid_range = fields.Char("Valid Range")
    sequence = fields.Integer("Sequence", default=1)