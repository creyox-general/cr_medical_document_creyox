# -*- coding: utf-8 -*-

from . import models
from . import wizards

from odoo import api, SUPERUSER_ID


def post_init(env):
    """Movein Demo record Creation."""


    movein_data = [{
        'name': 'Cred/Deb',
        'code': 3,
        'code_string': '3',
        'account_move_type': 'entry'},
        {
            'name': 'Income',
            'code': 100,
            'code_string': '100',
            'account_move_type': 'out_invoice'
        },
        {
            'name': 'Income',
            'code': 110,
            'code_string': '110',
            'account_move_type': 'out_refund'
        },
        {
            'name': 'Outcome',
            'code': 200,
            'code_string': '200',
            'account_move_type': 'in_invoice'
        },
        {
            'name': 'Outcome',
            'code': 210,
            'code_string': '210',
            'account_move_type': 'in_refund'
        }]
    movein = env['movement.code'].create(movein_data)
