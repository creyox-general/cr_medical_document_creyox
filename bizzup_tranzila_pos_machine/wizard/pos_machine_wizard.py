# -*- coding: utf-8 -*-

import requests
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PosMachineWizard(models.Model):
    """New custom model for physical terminal to make payment"""
    _name = 'pos.machine.wizard'
    _description = 'POS Machine Wizard'

    @api.model
    def _get_payment_limit(self):
        context = self._context
        invoice_record = self.env['account.move'].browse(
            context.get('active_id') if context.get(
                'active_model') == 'account.move' else '')
        sale_record = self.env['sale.order'].browse(
            context.get('active_id') if context.get(
                'active_model') == 'sale.order' else '')
        pos_id = self.env['tranzila.physical.terminal'].search([],
                                                               limit=1,
                                                               order='id ASC')
        record = invoice_record if invoice_record else sale_record
        payment_limit = 0
        if hasattr(record, 'payment_limit'):
            if record.payment_limit and int(record.payment_limit) > 0:

                payment_limit = int(record.payment_limit)
                selection_length = payment_limit
                # Creating the list of tuples
                selection_values = [(str(i), str(i)) for i in
                                    range(1, selection_length + 1)]
                return selection_values
            else:
                payment_limit = int(pos_id.provider_id.payment_limit)

                selection_length = payment_limit
                # Creating the list of tuples
                selection_values = [(str(i), str(i)) for i in range(1, selection_length + 1)]

                return selection_values

    physical_terminal_id = fields.Many2one('tranzila.physical.terminal',
                                           "POS Machine ID")
    payment_limit = fields.Selection(_get_payment_limit,
                                     string="Number Of Installment")
    currency_id = fields.Many2one('res.currency', "Currency")
    amount_to_charge = fields.Monetary('Amount To Charge',
                                       currency_field='currency_id')
    is_receipt = fields.Boolean("Is Receipt ?")


    @api.model
    def default_get(self, fields):
        res = super(PosMachineWizard, self).default_get(fields)
        context = self._context
        pos_id = self.env['tranzila.physical.terminal'].search([],
                                                               limit=1,
                                                               order='id ASC')
        res['is_receipt'] = True if context.get('active_model') == 'lyg.account.receipt' else False
        if pos_id:
            res['physical_terminal_id'] = pos_id.id
        if context.get('active_model') and context.get('active_id'):
            record = self.env[context.get('active_model')].browse(
                context.get('active_id'))
            record.action_confirm() if context.get(
                'active_model') == 'sale.order' else None
            if record:
                amount_to_charge = record.amount_total - record.amount_paid if context.get(
                    'active_model') == 'sale.order' and record.amount_total else record.amount_residual if context.get('active_model') == 'account.move' else record.total_pay_amount if context.get('active_model') == 'lyg.account.receipt' else 0
                if context.get('active_model') in ('account.move', 'sale.order'):
                    res['payment_limit'] = record.payment_limit if record.payment_limit else pos_id.provider_id.payment_limit
                res['amount_to_charge'] = amount_to_charge
        return res

    def _sale_invoice_create(self):
        context = self._context
        if context.get('active_model') == 'sale.order':
            record = self.env[context.get('active_model')].browse(
                context.get('active_id'))
            if record.state == 'draft':
                record.action_confirm()
            invoice = record.with_context(
                raise_if_nothing_to_invoice=False
                )._create_invoices()
            invoice.action_post()
            return invoice

    def generate_request_for_payment(self):
        api_url = self.physical_terminal_id.url
        context = self._context
        sale_invoice_id = self._sale_invoice_create() if context.get('active_model') == 'sale.order' else ''
        if not self.physical_terminal_id:
            raise ValidationError(
                _("You cannot pay without selecting the POS ID.")
            )
        record = self.env[context.get('active_model')].browse(
            context.get('active_id'))
        if record._name == 'account.move' and record.state == 'draft':
            record.action_post()
        if self.amount_to_charge == 0:
            raise ValidationError(
                _("The value of the payment amount must be positive.")
            )
        headersList = {
            "Content-Type": "application/json",
            "Connection": "keep-alive"
        }
        fpay = self.amount_to_charge / int(
            self.payment_limit if int(self.payment_limit) > 0 else 1)
        pre_spay = self.amount_to_charge - fpay
        spay = self.amount_to_charge - pre_spay
        try:
            if record._name == 'lyg.account.receipt' and record.is_credit_receipt:
                payload = {
                    "pos_id": self.physical_terminal_id.pos_id,
                    "currency": "376",
                    "cred_type": "1",
                    "supplier": self.physical_terminal_id.provider_id.supplier,
                    "tranmode": "C",
                    "sum": self.amount_to_charge
                }
            elif self.payment_limit:
                payload = {
                    "pos_id": self.physical_terminal_id.pos_id,
                    "currency": "376",
                    "cred_type": "8",
                    "npay": self.payment_limit,
                    "fpay": fpay,
                    "spay": spay,
                    "supplier": self.physical_terminal_id.provider_id.supplier,
                    "tranmode": "A",
                    "sum": self.amount_to_charge
                }
            else:
                payload = {
                    "pos_id": self.physical_terminal_id.pos_id,
                    "currency": "376",
                    "cred_type": "1",
                    "supplier": self.physical_terminal_id.provider_id.supplier,
                    "tranmode": "A",
                    "sum": self.amount_to_charge
                }
            response = requests.request("POST", api_url, json=payload,
                                        headers=headersList)
            feedback_data = response.json()
            _logger.info(
                "\n\n -------payload------- :\n%s",
                payload
            )
            _logger.info(
                "\n\n -------response------- :\n%s",
                feedback_data
            )
            transaction_result = feedback_data.get(
                'transaction_result') if feedback_data.get(
                'transaction_result') else ''
            if transaction_result and not transaction_result.get('statusCode') == 0:
                transaction = self.env['payment.transaction'].create({
                    'reference': record.name + " " + feedback_data.get(
                        'index') if feedback_data.get(
                        'index') else record.name,
                    'amount': self.amount_to_charge,
                    'partner_id': record.partner_id.id,
                    'invoice_ids': [(6, 0, (record.ids if context.get(
                        'active_model') == 'account.move' else sale_invoice_id.ids if sale_invoice_id else ''))],
                    'sale_order_ids': [(6, 0, (record.ids if context.get(
                        'active_model') == 'sale.order' else ''))],
                    'payment_method_id': self.env.ref('payment_tranzila.payment_methods_tranziila').id,
                    'provider_id': self.physical_terminal_id.provider_id.id,
                    'provider_reference': feedback_data.get('index'),
                    'currency_id': record.currency_id.id,
                    'operation': 'online_direct',
                    'npay': self.payment_limit,
                    'fpay': fpay,
                    'spay': spay,
                    'is_installment': True if int(
                        self.payment_limit) > 0 else False
                })
                if context.get('active_model') == 'lyg.account.receipt':
                    record.action_post_receipt()
                    transaction.payment_id = record.payment_ids.id
                    transaction.reference = record.name
                if transaction and not context.get('active_model') == 'lyg.account.receipt':
                    transaction._create_payment()
                transaction.update({
                    'state': 'done'
                })
            else:
                raise ValidationError(feedback_data)
        except Exception as e:
            raise ValidationError(e)
