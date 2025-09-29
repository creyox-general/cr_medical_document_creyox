# -*- coding: utf-8 -*-

{
    'name': 'Bizzup 85X Report Converters',
    'description': 'Upload and convert raw Hashavshevet SIXIN .dat files'
                   ' into PDF reports of records 60, 70 and 80 of report 856,'
                   ' or EFCIN .dat files into report 857.',
    'version': '18.0.1.6.5',
    'license': 'Other proprietary',
    'author': 'Lilach Gilliam',
    'website': 'https://bizzup.app',
    'depends': [
        'base',
        'account'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/menu_view.xml',
        'views/856_wizard_popup.xml',
        'views/857_wizard_popup.xml',
        'views/account_payment_view.xml',
        'views/856_dashboard.xml',
    ],
    'installable': True,
    'application': False,
}
