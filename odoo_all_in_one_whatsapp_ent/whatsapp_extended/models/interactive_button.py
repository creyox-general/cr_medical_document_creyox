from odoo import fields, models


class ButtonList(models.Model):
    _name = "interactive.button"
    _description = "Button for interactive components"

    title = fields.Char(string="Title")
    wa_interactive_id = fields.Many2one(comodel_name="wa.interactive.template")
