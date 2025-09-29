# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

{
    "name": "System 1000",
    "summary": "Enables exports to system 1000",
    "version": '18.0.1.0.0',
    "development_status": "Alpha",
    "category": "Accounting/Localizations",
    "website": "https://github.com/moshchot/BANKayma",
    'author': 'Gilliam Management Services and Information Systems, Ltd.',
    "maintainers": ["hbrunn"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "preloadable": True,
    "depends": [
        "account", "website_sale",

    ],
    "data": [
        "security/ir.model.access.csv",
        "wizards/l10n_il_system1000_export.xml",
        "views/res_company.xml",
        "views/product_template_views.xml",
    ],
    "demo": [],
}
