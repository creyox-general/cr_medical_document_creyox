# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    """Inherited ResPartner for new fields."""
    _inherit = 'res.partner'

    receipt_debit = fields.Integer("Receipt Debit", copy=False)
    receipt_credit = fields.Integer("Receipt Credit", copy=False)
