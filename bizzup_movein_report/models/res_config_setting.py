# -*- coding: utf-8 -*-

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_for_rivhit = fields.Boolean(
        "Print for Rivhit",
        config_parameter="bizzup_movein_report.is_for_rivhit"
    )
    is_for_hrp = fields.Boolean(
        "Print for HRP",
        config_parameter="bizzup_movein_report.is_for_hrp"
    )
