#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################
from . import models
from odoo import api, SUPERUSER_ID

def post_init(env):
    """Company write"""
    # env = api.Environment(cr, SUPERUSER_ID, {})
    company_id = env.user.company_id.search([('account_fiscal_country_id.code', '=', 'IL')], limit=1)
    if company_id:
        company_id.write({
            'is_l10n_installed': True,
        })
    if company_id and company_id.is_l10n_installed:
        journal_obj = env['account.journal'].search([('type', 'not in', ['bank', 'cash'])])
        for journal in journal_obj:
            journal.update({'restrict_mode_hash_table': True})
