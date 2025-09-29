# -*- coding: utf-8 -*-

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    """Inherited ResConfigSetting for new fields"""
    _inherit = 'res.config.settings'

    vat_limit = fields.Integer(
        "VAT Limit",
        config_parameter="l10n_il_lyg.vat_limit"
    )
