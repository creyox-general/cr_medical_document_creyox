# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential. For more information, please contact lg@bizzup.app

from odoo import models, api


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override the create method to automatically generate related financial history
        records when customer invoices (move_type = 'out_invoice') are created.
        """
        moves = super().create(vals_list)
        out_invoices = moves.filtered(lambda m: m.move_type == "out_invoice")
        if out_invoices:
            self.env["financial.history"].create(
                [{"invoice_id": move.id} for move in out_invoices]
            )
        return moves
