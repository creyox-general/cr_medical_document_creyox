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
    "depends": ["base", "contacts", "sale_management", "icd_manager"],
    "data": [
        "security/ir.model.access.csv",
        "data/cretificate_expiration_reminnder_template.xml",
        "data/ir_cron.xml",
        "views/medical_record_view.xml",
        "views/medical_record_tag_view.xml",
        "views/medical_services_view.xml",
        "views/private_insurance_view.xml",
        "views/private_insurence_tag_view.xml",
        "views/res_partnner_inherited.xml",
        "views/hr_employee_inherited.xml",
        "views/medical_vitals_item_view.xml",
        "wizard/search_detials_wizard_view.xml",
        "reports/visit_details_report_action.xml",
        "reports/visit_details_report_header.xml",
        "reports/visit_details_report_template.xml",
        "reports/report_prescription.xml",
    ],
    "application": True,
    "installable": True,
}
