#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################

{
    'name': 'LYG Israel - Accounting',
    "version": "18.0.1.1.0",
    'category': 'Localization',
    'summary': """This is the latest basic Israelian localisation necessary to run Odoo in Israel""",
    'description': """
This is the latest basic Israeli localisation necessary to run Odoo in Israel:
================================================================================

This module consists of:
 - Generic Israeli chart of accounts
 - Israeli taxes and tax report
 - Fiscal positions for retention / Palestina]
 """,
    "license": "Other proprietary",
    "author": "Yves Goldberg (Ygol InternetWork)",
    "website": "http://www.ygol.com",
    'depends': ['l10n_il', 'partner_bank_code'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'data/ita_branch_list.xml',
        'data/l10n_il_tax_reason_data.xml',
        'data/res_bank.xml',
        'views/account_tax_views.xml',
        'views/res_partner_views.xml',
        'views/res_company_views.xml',
        'views/report_invoice.xml',
        'views/account_journal_view.xml',
    ],
    'auto_install': True,
    'post_init_hook': 'post_init',
}
