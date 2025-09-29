# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app
{
    "name": "Biuld ASCII Report for Vendo bill",
    "summary": """Biuld ASCII Report for Vendo bill""",
    "description": """ HT00364 - Biuld ASCII Report for Vendo bill
    HT01851
    """,
    "author": "Gilliam Management Services and Information Systems, Ltd.",
    "website": "https://www.bizzup.app/",
    "category": "Accounting",
    "version": "18.0.1.6.1",
    "depends": ["accountant", "account"],
    "license": "AGPL-3",
    "installable": True,
    "application": True,
    "data": [
        "security/ir.model.access.csv",
        "views/res_company_views.xml",
        "views/account_payment_views.xml",
        "views/res_config_settings_views.xml",
        "wizard/vender_bill_ascii_report_wizard.xml",
        "report/text_report.xml",
    ],
}
