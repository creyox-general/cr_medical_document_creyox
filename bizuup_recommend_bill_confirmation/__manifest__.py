# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

{
    "name": "Bizzup Recommmend Bill Confirmation",
    "description": """"
        Ticket :  HT01880
        When a user adds the confirmation number to a bill
        I want to add a notification that says to the user "it will be better to add last 9 digits"
        This error will pop up when the confirmation number is longer than 10 digits""",
    "version": "18.0.1.0.0",
    "license": "Other proprietary",
    "author": "Gilliam Management Services and Information Systems",
    "website": "https://bizzup.app",
    "depends": ["account","oii_israel_invoices"],
    "data": {
        "views/account_move_views.xml",
    },
    "installable": True,
    "auto_install": False,
    "application": False,
}
