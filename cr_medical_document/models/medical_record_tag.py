# -*- coding: utf-8 -*-
# Part of Creyox Technologies

from odoo import fields, models, api, _


class MedicalRecordTag(models.Model):
    _name = "medical.record.tag"
    _description = "Medical Record Tag"

    name = fields.Char(string="Name")
    color = fields.Integer(string="Color", default=0)