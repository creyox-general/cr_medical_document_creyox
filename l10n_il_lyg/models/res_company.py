# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _name = 'res.company'
    _description = 'Companies'
    _inherit = 'res.company'

    l10n_il_withh_tax_id_number = fields.Char(string='WHT ID', readonly=False,
                                              default='XXX-XX-XXXX')
    is_l10n_installed = fields.Boolean()
