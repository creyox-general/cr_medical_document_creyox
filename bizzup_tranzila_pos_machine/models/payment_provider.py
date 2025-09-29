# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _


class PaymentProviderTranzila(models.Model):
    _inherit = 'payment.provider'

    tranzila_terminal_ids = fields.One2many('tranzila.physical.terminal',
                                            'provider_id')
