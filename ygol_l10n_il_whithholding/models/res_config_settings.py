#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    withholding_tax_account_id = fields.Many2one(
        'account.account', related='company_id.withholding_tax_account_id',
        readonly=False,
        string="Vendor Withholdingtax Account",
        domain="[('company_id', '=', company_id)]",
        help='The account of vendor withholding')
    cust_withholding_tax_account_id = fields.Many2one(
        'account.account',
        related='company_id.cust_withholding_tax_account_id',
        readonly=False, string='Customer Withholdingtax Account',
        domain="[('company_id', '=', company_id)]")
