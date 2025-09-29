# -*- coding: utf-8 -*-

{
    'name': 'Bizzup Movein Report',
    "description": """
        This module generates a report that includes all the accounting
        information of odoo and report is compatible for Rivhit and HRP.""",
    'version': '18.0.2.0.0',
    'license': 'Other proprietary',
    'author': 'Lilach Gilliam',
    'website': 'https://bizzup.app',
    'depends': [
        'base',
        'account',
        'payment',
        'lyg_receipt',
        'point_of_sale',
    ],
    'data': {
        'security/ir.model.access.csv',
        # 'data/movement_code_data.xml',
        'views/res_config_settings_views.xml',
        'views/account_account_views.xml',
        'views/account_move_views.xml',
        'views/account_payment_views.xml',
        'views/res_partner_views.xml',
        'views/movement_code_views.xml',
        'wizards/movein_report_wizard_views.xml',
        'reports/movein_report.xml',
        'reports/movein_prm.xml',
    },
    'application': True,
    "post_init_hook": 'post_init',
    'installable': True,
}
