# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    """Inherited Sale Order for new fields."""
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super().action_confirm()
        if not self.order_line:
            raise ValidationError(
                _("Please add a line before confirming the sale order."))
        if not self.partner_id.vat:
            raise ValidationError(
                _("Please select a partner with VAT ID")
            )
        for rec in self.order_line:
            if not rec.product_id:
                raise ValidationError(
                    _("Please add proper product before confirming the order."))
        return res
