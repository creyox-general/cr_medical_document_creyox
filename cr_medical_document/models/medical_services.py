# -*- coding: utf-8 -*-
# Part of Creyox Technologies

from odoo import fields, models, api, _


class MedicalServices(models.Model):
    _name = "medical.services"
    _description = "Medical Services"

    name = fields.Char(string="All Medical Service Provided")