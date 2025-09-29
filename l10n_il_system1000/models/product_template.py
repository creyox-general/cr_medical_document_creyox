# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = 'product.template'

    productUrl = fields.Char(
        string='Product Url',
        store=True
        )
    discount = fields.Float(
        string='Discount',
        compute='_computed_price',
        store=True,
        readonly=False
        )

    @api.depends('list_price', 'compare_list_price')
    def _computed_price(self):
        for record in self:
            if record.compare_list_price:
                record.discount = ((record.compare_list_price - record.list_price) / record.compare_list_price) * 100
            else:
                record.discount = 0
