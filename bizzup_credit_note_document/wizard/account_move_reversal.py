# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def reverse_moves(self, is_modify=False):
        """
        Purpose:
            When creating a credit note from an account move reversal,
            force the custom document type fields to default to "Regular"
            values, regardless of what was set on the original move.

        Fields set:
            - transaction_type_document_out_invoice = "S" (Regular Sale)
            - transaction_type_document_in_invoice  = "T" (Regular Supplier)

        Args:
            is_modify (bool): Whether the reversal is in modify mode.

        Returns:
            dict: Action dict returned by super().
        """
        res = super().reverse_moves(is_modify=is_modify)

        credit_note_id = res.get('res_id')
        credit_note = self.env['account.move'].browse(credit_note_id)

        # Force default selection values
        credit_note.transaction_type_document_out_invoice = "S"
        credit_note.transaction_type_document_in_invoice = "T"

        return res
