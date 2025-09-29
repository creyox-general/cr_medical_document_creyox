# -*- coding: utf-8 -*-
from odoo import models, fields


class PosSessionReportHistory(models.Model):
    _name = "pos.session.report.history"
    _description = "Pos Session Report History"

    pos_id = fields.Many2one("pos.session")
    user_id = fields.Many2one("res.users")
    report_print_time = fields.Datetime(string="Time")
