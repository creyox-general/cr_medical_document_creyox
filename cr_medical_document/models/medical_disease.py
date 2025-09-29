# -*- coding: utf-8 -*-
# Part of Creyox Technologies

from odoo import fields, models, api, _


class MedicalDisease(models.Model):
    _inherit = "medical.disease"
    _rec_name = "procedure_name"

    procedure_name = fields.Many2one('medical.record', string="Procedure Name")
    nomed_code = fields.Char(string="Nomed Code")