# -*- coding: utf-8 -*-
# Part of Creyox Technologies

from odoo import fields, models, api, _


class PrivateInsuranceTag(models.Model):
    _name = "private.insurance.tag"
    _description = "Private Insurance"

    name = fields.Char(string="Private Insurance Tags")
    color = fields.Integer(string="Color", default=0)