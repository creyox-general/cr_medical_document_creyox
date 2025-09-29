#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################
from odoo import api, SUPERUSER_ID
from . import models, wizard, controllers


def post_init(env):
    """Company write"""

    # env = api.Environment(cr, SUPERUSER_ID, {})
    company_id = env.user.company_id.search(
        [('account_fiscal_country_id.code', '=', 'IL')], limit=1)
    if company_id:
        company_id.write({
            'receipt_restrict_mode_hash': True,
        })
