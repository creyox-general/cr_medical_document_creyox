#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    receipt_count = fields.Integer(
        string="Receipts",
        compute="get_receipts",
        groups="account.group_account_invoice"
    )

    def action_receipt(self):
        """
        Method to return a receipts list view
        """
        return {
            "type": "ir.actions.act_window",
            "res_model": "lyg.account.receipt",
            "domain": [('partner_id', '=', self.id)],
            "name": "Receipts",
            "view_mode": "list,form",
        }

    def get_receipts(self):
        """
        Compute Method to return count of receipts
        """
        for rec in self:
            receipt = self.env['lyg.account.receipt'].search(
                [('partner_id', '=', rec.id)]
            ).ids
            rec.receipt_count = len(receipt)
