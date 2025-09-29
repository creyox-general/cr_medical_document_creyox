# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential. For more information, please contact lg@bizzup.app
from tokenize import String

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FinancialHistory(models.Model):
    _name = "financial.history"
    _description = "Financial History"
    _order = "date desc"
    _rec_name = 'partner_id'

    partner_id = fields.Many2one("res.partner",
                                 string="Contact", compute="_compute_partner_id", store=True)
    account_id = fields.Char(string="Account ID")
    date = fields.Datetime(string="CreatedOn")
    document_id = fields.Char(string="Document ID")
    document_type = fields.Selection([
        ('13', 'הזמנות'),
        ('81', 'חשבונית מס'),
        ('82', 'חשבונית עסקה'),
        ('83', 'קבלות'),
        ('84', 'חשבונית מס/קבלה'),
        ('85', 'חשבונית זיכוי'),
    ], string='Document Type')
    # HT01938
    # Set the value from the `invoiceid` column into the `document_fireberry_id`
    # field during import, so the related field has been removed and replaced
    # with a simple field.
    document_fireberry_id = fields.Char(string="Document fireberry ID")
    description = fields.Char(
        string="Description")
    amount_total = fields.Float(
        string="Total Amount"
    )
    total_payment = fields.Float(
        string="Total Payment"
    )
    products_total = fields.Float(
        string="Products Total"
    )
    tax_value = fields.Float(
        string="Tax Value"
    )
    tax_percentage = fields.Char(
        string="Tax Percentage"
    )

    @api.depends('account_id')
    def _compute_partner_id(self):
        """
        This method searches for a partner whose custom field
        'x_studio_account_id' matches the current record's account_id.
        If found, assigns the partner to the partner_id field.
        If account_id is not set or no matching partner is found,
        partner_id is set to False.
        """
        for rec in self:
            if rec.account_id:
                partner = self.env['res.partner'].search(
                    [('x_studio_account_id', '=', rec.account_id)],
                    limit=1
                )
                rec.partner_id = partner
            else:
                rec.partner_id = False
