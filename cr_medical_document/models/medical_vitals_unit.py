# -*- coding: utf-8 -*-
# Part of Creyox Technologies

from odoo import fields, models, api, _


class MedicalVitalsUnit(models.Model):
    _name = "medical.vitals.unit"
    _description = "Medical Vitals Unit"

    name = fields.Char(string="Name")