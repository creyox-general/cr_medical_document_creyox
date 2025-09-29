from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    discount_product = fields.Boolean("Is Discount Product ?")
