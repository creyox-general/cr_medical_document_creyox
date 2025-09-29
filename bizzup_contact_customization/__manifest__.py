# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

{
    "name": "Bizzup Contact Customization",
    "description": """ 
        Ticket : HT01720
        Introduced a 'TAZ' field on the Contact (res.partner) 
        model with soft validation for 9-digit numeric input.
    """,
    "version": "18.0.1.0.0",
    "category": "Contacts",
    "license": "Other proprietary",
    "author": 'Gilliam Management Services and Information Systems, Ltd.',
    "website": "www.bizzup.app",
    "depends": ["contacts"],
    "data": [
        "views/res_partner_view.xml"
    ],
    "installable": True,
    "application": False,
}
