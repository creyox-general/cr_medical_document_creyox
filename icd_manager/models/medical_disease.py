# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MedicalDisease(models.Model):
    _name = "medical.disease"
    _description = "Medical disease"

    code = fields.Char(string='Code')
    name = fields.Char(string='Short name')
    long_name = fields.Char(string='Long name')
