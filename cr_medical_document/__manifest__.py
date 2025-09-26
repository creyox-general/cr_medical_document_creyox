# -*- coding: utf-8 -*-
# Part of Creyox Technologies.
{
    "name": "Medical Documentations | Patient Medical Records",
    "author": "Creyox Technologies",
    "website": "https://www.creyox.com",
    "support": "support@creyox.com",
    "summary": """
        This module is designed to maintain the Patient Medical Records.
    """,
    "version": "18.0.0.0",
    "license": "LGPL-3",
    "description": """
        This module is designed to maintain the Patient Medical Records.
    """,
    "depends": ["base", "contacts", "sale_management"],
    "data": [
        "security/ir.model.access.csv",
        "views/medical_record_view.xml",
        "views/medical_record_tag_view.xml"
    ],
    "application": True,
    "installable": True,
}
