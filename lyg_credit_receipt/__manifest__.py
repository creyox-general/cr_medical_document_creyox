#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################
{
    "name": "LYG Credit Receipt",
    "description": """
        This module add multiple payment for receipt""",
    "version": "18.0.1.2.0",
    "category": "Invoicing",
    "license": "Other proprietary",
    "author": "Yves Goldberg (Ygol InternetWork)",
    "website": "http://www.ygol.com",
    "depends": [
        "ygol_l10n_il_whithholding",
        "payment",
        "portal",
        "lyg_receipt",
    ],
    "data": [
        "data/credit_receipt_sequence_data.xml",
        "views/account_credit_receipt_views.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
}
