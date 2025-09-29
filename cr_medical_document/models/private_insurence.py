# -*- coding: utf-8 -*-
# Part of Creyox Technologies

from odoo import fields, models, api, _


class PrivateInsurance(models.Model):
    _name = "private.insurance"
    _description = "Private Insurance"

    name = fields.Char(string="Private Insurance Type")
    tag = fields.Many2many('private.insurance.tag', string="Tags")