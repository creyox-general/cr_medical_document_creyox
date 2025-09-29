# -*- coding: utf-8 -*-

import requests
import pprint
import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class TranzilaPhysicalTerminal(models.Model):
    """New custom model for physical terminal."""
    _name = 'tranzila.physical.terminal'
    _description = 'Tranzila Physical Terminal'
    _rec_name = 'pos_id'

    pos_id = fields.Char("Machine ID", copy=False)
    url = fields.Char("URL",
                      default='https://secure5.tranzila.com/cgi-bin/tranzila71mdl.cgi')
    company_id = fields.Many2one('res.company', string="Company")
    provider_id = fields.Many2one('payment.provider', string="Provider")

    def check_machine_connection(self):
        if self.provider_id.code != 'tranzila':
            return
        api_url = self.url
        headersList = {
            "Content-Type": "application/json",
            "Connection": "keep-alive"
        }
        payload = {
             "pos_id": self.pos_id,
             "currency": "376",
             "cred_type": "1",
             "supplier": self.provider_id.supplier,
             "tranmode": "A",
             "sum": "1"
        }
        response = requests.request("POST", api_url, json=payload,
                                    headers=headersList)
        feedback_data = response.json()
        _logger.info("entering _handle_feedback_data with data:\n%s",
                     pprint.pformat(feedback_data))
        transaction_result = feedback_data.get('transaction_result') if feedback_data.get('transaction_result') else ''
        if feedback_data.get('status') == 0 and transaction_result.get(
                'statusCode') == 0:
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Successful'),
                    'type': 'success',
                    'message': 'Successfully Connected with Machine',
                    'sticky': True,
                }
            }
            return notification
        else:
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection is not Good'),
                    'type': 'danger',
                    'message': transaction_result.get('statusMessage') if transaction_result else feedback_data.get('error'),
                    'sticky': True,
                }
            }
            return notification

