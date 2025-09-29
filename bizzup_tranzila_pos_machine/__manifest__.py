# -*- coding: utf-8 -*-

{
    "name": "Bizzup Tranzila Physical Termina",
    "summary": """Payment Acquirer: Payment Tranzila POS Machine Terminal""",
    "description": """Payment Tranzila POS Machine Terminal""",
    "license": "Other proprietary",
    "author": "Lilach Gilliam",
    "website": "https://bizzup.app",
    "category": 'Accounting/Payment',
    "version": '18.0.1.0.0',
    "depends": [
        'base',
        'account',
        'sale',
        'bizzup_tranzila_receipt_updates',
        'payment_tranzila',
    ],
    "data": [
        'security/ir.model.access.csv',
        'wizard/pos_machine_wizard_views.xml',
        'views/account_move_views.xml',
        'views/sale_order_views.xml',
        'views/payment_provider_views.xml',
        'views/tranzila_physical_terminal.xml',
        'views/lyg_receipt_views.xml',
    ],
    "installable": True,
}
