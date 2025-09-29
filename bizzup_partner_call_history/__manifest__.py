# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential. For more information, please contact
# lg@bizzup.app

{
    'name': 'Bizzup Partner Call History',
    "version": "18.0.1.0.6",
    "description": "Track and store call history related to partners (contacts). "
                   "Includes call metadata, recording URL, duration "
                   "Adds a Call History tab to contact forms and a separate menu in Contacts > Configuration.",
    "license": "Other proprietary",
    "author": "Gilliam Management Services and Information Systems, Ltd.",
    "website": "https://bizzup.app",
    'depends': ['base', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/partner_call_history_view.xml',
        'views/res_partner.xml',
    ],

    "assets": {"web.assets_backend": [
        "bizzup_partner_call_history/static/src/xml/call_history_list_buttons.xml",
        "bizzup_partner_call_history/static/src/js/call_history_list_controller.js",
        ],
    },

    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
