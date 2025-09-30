# -*- coding: utf-8 -*-
# Part of Creyox Technologies

from odoo import fields, models, api, _


class MedicalVitalsItems(models.Model):
    _name = "medical.vitals.items"
    _description = "Medical Vitals Items"

    name = fields.Char(string="Item", required=True)
    unit_id = fields.Many2one('medical.vitals.unit', string="Default Unit")
    min_range = fields.Char(string="Minimum Range")
    max_range = fields.Char(string="Maximum Range")