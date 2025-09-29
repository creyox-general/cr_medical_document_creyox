#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################
from . import models
from . import report

from odoo import api, SUPERUSER_ID


def post_init(env):
    """HMK journal creation"""
    # env = api.Environment(env, SUPERUSER_ID, {})

    company = env['res.company'].search(
        [('account_fiscal_country_id.code', '=', 'IL')], limit=1)

    if company:
        hmk_journal_data = {
            'name': 'Invoice Receipt',
            'code': 'HMK',
            'type': 'sale',
            'is_hmk': True,
            'company_id': company.id
        }
        existing_journal = env['account.journal'].search([('code', '=', 'HMK')])
        if not existing_journal:
            journal = env['account.journal'].create(hmk_journal_data)
