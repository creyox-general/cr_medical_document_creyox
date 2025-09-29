# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
{
    "name": "LYG Unified Reporting",
    "description": """
        Generate the unified reporting required in Israel""",
    "version": "18.0.1.0.0",
    "category": "Accounting & Finance",
    "author": "Yves Goldberg (Ygol InternetWork)",
    "website": "http://www.ygol.com",
    "license": "Other proprietary",
    "depends": [
        "lyg_hmk",
        "lyg_receipt",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_company_views.xml",
        "views/account_payment_view.xml",
        "views/product_view.xml",
        "wizard/unified_report_view.xml",
        "report/data_extraction_summary_template.xml",
        "report/data_extraction_summary_report.xml",
        "report/unified_report_template.xml",
        "report/unified_report_2_6_report.xml",
        "report/unified_report_2_6_template.xml",
        "views/account_move_view.xml",
    ],
    "demo": [
        "demo/product_demo.xml",
        "demo/res_company_demo.xml",
    ],
    "installable": True,
    "application": True,
}
