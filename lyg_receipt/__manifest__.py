#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################
{
    "name": "LYG Receipt",
    "description": """
        This module add multiple payment for receipt""",
    "version": "18.0.1.3.6",
    "category": "Invoicing",
    "license": "Other proprietary",
    "author": "Yves Goldberg (Ygol InternetWork)",
    "website": "http://www.ygol.com",
    "depends": [
        "ygol_l10n_il_whithholding",
        "payment",
        "portal",
    ],
    "data": [
        'security/ir.model.access.csv',
        'security/receipt_security.xml',
        'data/receipt_sequence_data.xml',
        'data/ir_cron_data.xml',
        'views/account_receipt_view.xml',
        'views/res_company_view.xml',
        'views/portal_view.xml',
        'views/account_move_view.xml',
        'views/account_payment_view.xml',
        'views/res_partner_view.xml',
        'report/receipt_report.xml',
        'data/mail_template.xml',
        'wizard/payment_register_view.xml',
        'views/res_config_settings_view.xml',
    ],
    "demo": [],
    "installable": True,
    "application": False,
    'post_init_hook': 'post_init',
}
