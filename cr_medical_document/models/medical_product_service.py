# -*- coding: utf-8 -*-
# Part of Creyox Technologies

from odoo import fields, models, api, _


class MedicalPrescription(models.Model):
    _name = "medical.product.service"
    _description = "Medical Prescription"

    medical_document_id = fields.Many2one('medical.record', string="Medical Document")
    product_id = fields.Many2one('product.template', string="Product Name")
    product_qty = fields.Integer(string="Quantity")
    product_price = fields.Float(string="Price")
    total = fields.Float(string="Quantity")