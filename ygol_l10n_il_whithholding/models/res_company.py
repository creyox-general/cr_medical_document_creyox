#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################
from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = "res.company"

    company_status = fields.Selection([
        ('company', 'Company'),
        ('single_person', 'Single Person'),
        ('partnership', 'Partnership'),
        ('ngo', 'NGO'), ('state_company', 'State Company')])
    withholding_tax_process = fields.Boolean("Withholding Payment Process ?")
    withholding_tax_account_id = fields.Many2one('account.account',
                                                 string='Vendor Withholdingtax Account')
    cust_withholding_tax_account_id = fields.Many2one('account.account',
                                                      string='Customer Withholdingtax Account')
    def_withholding_tax_rate = fields.Float("Default Withholding Tax(%)",
                                            default=30.0)

    def write(self, vals):
        res = super(ResCompany, self).write(vals)
        if vals.get('def_withholding_tax_rate'):
            res_partner_obj = self.env['res.partner'].search(
                [('country_id.code', '=', 'IL')])
            res_partner_obj.update({
                'withholding_tax_rate': vals.get('def_withholding_tax_rate')
            })
        return res
