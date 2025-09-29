# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential. For more information, please contact lg@bizzup.app

from odoo import models, fields, api


class ResPartner(models.Model):
    """Extends res.partner to include financial history tracking and total amount summary."""

    _inherit = "res.partner"

    financial_history_ids = fields.One2many(
        "financial.history", "partner_id", string="Financial History"
    )

    total_financial_amount = fields.Monetary(
        string="Total Financial Amount",
        compute="_compute_total_financial_amount"
    )

    def do_nothing(self):
        """Placeholder method that performs no action (used for smart button binding)."""
        return

    @api.depends("financial_history_ids")
    def _compute_total_financial_amount(self):
        """Compute the total financial amount from related financial history records."""
        for partner in self:
            history = partner.financial_history_ids
            total = sum(history.mapped("amount_total"))
            partner.total_financial_amount = total
