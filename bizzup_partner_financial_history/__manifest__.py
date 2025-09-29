# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

{
    "name": "Bizzup Partner Financial History",
    "description": """
        Ticket : HT01658
        This module adds financial history tracking for partners by recording
        and displaying outgoing invoice data
        (untaxed, tax, and total amounts). It includes:        
            - A dedicated model for financial history entries.
            - Real-time updates when invoices are created.
            - Display of aggregated financial totals in the contact form.
            - Smart button integration for quick access to financial summary.
        Ticket : HT01938
        Set the value from the `invoiceid` column into the `document_fireberry_id` 
        field during import, so the related field has been removed and replaced 
        with a simple field.
        """,
    "version": "18.0.1.0.5",
    "license": "Other proprietary",
    "author": "Gilliam Management Services and Information Systems, Ltd.",
    "website": "https://bizzup.app",
    "depends": ["contacts", "account"],
    "data": [
        "security/ir.model.access.csv",
        "views/financial_history_views.xml",
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "application": False,
}
