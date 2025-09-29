from odoo import fields, models


class WAInteractiveTemplate(models.Model):
    _name = "wa.interactive.template"
    _description = "Whatsapp Interactive Template Features"

    wa_template_id = fields.Many2one(comodel_name="whatsapp.template")
    interactive_type = fields.Selection(
        [
            ("button", "BUTTON"),
            ("list", "LIST"),
            ("product", "PRODUCT"),
            ("product_list", "PRODUCT LIST"),
        ],
        "Interactive Message Type",
        default="button",
    )
    interactive_list_ids = fields.One2many(
        comodel_name="interactive.list.title",
        inverse_name="wa_interactive_id",
        string="List Items",
    )
    interactive_button_ids = fields.One2many(
        comodel_name="interactive.button",
        inverse_name="wa_interactive_id",
        string="Button Items",
    )
    interactive_product_list_ids = fields.One2many(
        comodel_name="interactive.product.list",
        inverse_name="wa_interactive_id",
        string="Product List Items",
    )
    catalog_id = fields.Char(string="Catalog ID")
    product_retailer_id = fields.Char(string="Product Retailer ID")
