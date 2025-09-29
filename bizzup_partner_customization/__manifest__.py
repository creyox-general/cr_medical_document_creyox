# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app
# -*- coding: utf-8 -*-

{
    'name': 'Bizzup Partner Customization',
    "description": """
        This module will add a field to the partner model to store the Bizzup
        partner ID.
    """,
    'version': '18.0.1.0.0',
    'license': 'Other proprietary',
    'author': 'Gilliam Management Services and Information Systems, Ltd.',
    'website': 'https://bizzup.app',
    'depends': [
        'base',
    ],
    'data': {
        'views/res_partner_views.xml',
    },
    'application': True,
    'installable': True,
}