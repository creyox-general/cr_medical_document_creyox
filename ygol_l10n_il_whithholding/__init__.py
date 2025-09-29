#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################
from . import models, wizard
from odoo import api, SUPERUSER_ID


def post_init(env):
    """Company write"""
    # env = api.Environment(cr, SUPERUSER_ID, {})
    company_id = env.user.company_id.search([('account_fiscal_country_id.code', '=', 'IL')], limit=1)
    if env.user.company_id.is_l10n_installed:
        account_111200 = env.ref(f'l10n_il.{company_id.id}_il_account_111200',
                raise_if_not_found=False)
        account_111230 = env.ref(f'l10n_il.{company_id.id}_il_account_111230',
                raise_if_not_found=False)
        if account_111200 and account_111230:
            withholding_tax_account_id = env['account.account'].search([('id','=', account_111200.id)])
            cust_withholding_tax_account_id = env['account.account'].search([('id', '=', account_111230.id)])
            if company_id and withholding_tax_account_id and cust_withholding_tax_account_id:
                company_id.write({
                    'withholding_tax_process': True,
                    'withholding_tax_account_id': withholding_tax_account_id.id,
                    'cust_withholding_tax_account_id': cust_withholding_tax_account_id.id
                })
        else:
            new_withholding_tax_account_id = env['account.account'].create({
                'code': '111200V',
                'name': 'Income tax withheld - vendors',
                'account_type': 'liability_current',
            })

            new_cust_withholding_tax_account_id = env['account.account'].create({
                'code': '111230C',
                'name': 'Income tax withheld - customers',
                'account_type': 'liability_current',
            })
            if company_id:
                company_id.write({
                    'withholding_tax_process': True,
                    'withholding_tax_account_id': new_withholding_tax_account_id.id,
                    'cust_withholding_tax_account_id': new_cust_withholding_tax_account_id.id,
                })

