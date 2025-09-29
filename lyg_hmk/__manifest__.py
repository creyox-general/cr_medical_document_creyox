#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################

{
    "name": "LYG HMK",
    "summary": "This Module is managing HMK type invoice",
    "description": """
        This module add tax invoice receipt to odoo invoicing""",
    "version": "18.0.1.0.0",
    "category": "Invoicing",
    "license": "Other proprietary",
    "author": "Yves Goldberg (Ygol InternetWork)",
    "website": "http://www.ygol.com",
    "depends": ["ygol_l10n_il_whithholding"],
    "data": [
        "security/ir.model.access.csv",
        "views/account_move_view.xml",
        "views/account_journal.xml",
        "report/hmk_report_invoice_with_payments.xml",
    ],
    'demo': [
        'demo/res_partner_demo.xml',
        'demo/account_invoice_500_lines.xml',
    ],
    "installable": True,
    "post_init_hook": 'post_init',
    "application": True,
}
