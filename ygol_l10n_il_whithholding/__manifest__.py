#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################
{
    "name": "LYG Withholding",
    "description": """
        This module add receipt in tranzila document""",
    "version": "18.0.1.0.0",
    "category": "Invoicing",
    "license": "Other proprietary",
    "author": "Yves Goldberg (Ygol InternetWork)",
    "website": "http://www.ygol.com",
    "depends": ["l10n_il_lyg"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron_data.xml",
        "views/res_partner_view.xml",
        "views/res_company_view.xml",
        "views/account_move_views.xml",
        # "views/res_config_settings_view.xml",
        "views/account_payment_view.xml",
        "wizard/withholding_system_wizard.xml",
        "report/account_report_view.xml"
    ],
    'demo': [
    ],
    "installable": True,
    'post_init_hook': 'post_init',
    "application": False,
    "auto_install": True,
}
