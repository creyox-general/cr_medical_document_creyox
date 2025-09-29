# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountPayment(models.Model):
    _inherit = "account.payment"

    is_deposited = fields.Boolean(
        string="Deposited ?"
    )
    validity_date = fields.Date(
        string="Validity Date"
    )
    is_refund = fields.Boolean(
        string="Refund"
    )

    def make_deposite(self):
        """
        Marks the record as deposited if it is not already marked.
        """
        for rec in self:
            if rec.is_deposited is not True:
                rec.is_deposited = True
