{
    "name": "Bizzup Deposite Report",
    "summary": """
        User Story: HT01195
        Bizzup Deposite Report.
    """,
    "version": "18.0.1.6.0",
    "license": "Other proprietary",
    "author": "",
    "website": "",
    "depends": ["lyg_receipt", 'account_reports'],
    "data": [
        'security/ir.model.access.csv',
        'reports/deposite_report_template.xml',
        'reports/deposite_reports.xml',
        'views/account_payment_views.xml',
        'wizard/deposite_report_wizard_views.xml',
    ],
    "application": True,
    "installable": True,
}
