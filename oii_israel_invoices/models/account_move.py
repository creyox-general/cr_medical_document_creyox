from odoo import _, fields, models, api
from odoo.exceptions import UserError, ValidationError
from .utils import CONSTS

import logging

_logger = logging.getLogger(__name__)

GET_MOVE_TYPE_NUMBER = {
    'out_invoice': 305,
    'il_invoice_receipt': 320,
    'out_refund': 330,
}


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'oii.invoices.base']

    rt_confirmation_number = fields.Char(string='Confirmation Number', copy=False)
    rt_tax_call_counter = fields.Integer(string='# API Calls', copy=False)
    rt_number_approved = fields.Boolean(string='Number Approved', copy=False)
    rt_taxes_minimum_untaxed_amount = fields.Integer(related='company_id.rt_taxes_minimum_untaxed_amount', copy=False)
    enable_taxes_integration = fields.Boolean(related='company_id.enable_taxes_integration', copy=False)

    def action_post(self):
        res = super(AccountMove, self).action_post()
        company = self.env.company
        if company.enable_taxes_integration:
            # HT02023
            # Converted 'Amount Untaxed' to company currency and then comparing it with Company's minimum untaxed amount
            needs_confirmation_number = self.filtered(
                lambda x: x.move_type in ['out_invoice', 'out_refund', 'il_invoice_receipt']
                          and not x.rt_confirmation_number
                          and x.currency_id._convert(
                    x.amount_untaxed,
                    company.currency_id,
                    company,
                    x.invoice_date or x.date or fields.Date.today()) >= company.rt_taxes_minimum_untaxed_amount
                          and x.amount_tax
            )
            for move in needs_confirmation_number:
                action = move.get_conf_number()
                if action['params']['type'] == 'danger':
                    raise ValidationError(f'Failed to receive confirmation number:\n {action["params"]["message"]}')
        return res

    def get_conf_number(self):
        def parse_error_message(message):
            error_messages = []
            if message.get("errors"):
                for error in message["errors"]:
                    error_messages.append(error["message"])
            return error_messages

        self.ensure_one()
        endpoint = 'Invoices/v2/Approval'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {token}'.format(token=self.env.company.rt_taxes_access_token),
        }
        values = self.prepare_invoice_details()

        self.write({'rt_tax_call_counter': self.rt_tax_call_counter + 1})
        status, response = self._do_request(endpoint, params=values, headers=headers, method='POST', type='invoice',
                                            need_json_dump=True)

        action = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'danger',
                'title': _('Failure'),
                'message': '',
                'sticky': True,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
        if status == 200:
            conf_number = response.get('confirmation_number', '')
            approved = response.get('approved', False)
            if approved and conf_number:
                self.rt_confirmation_number = conf_number
                self.rt_number_approved = True
                action['params'].update({
                    'type': 'success',
                    'title': _('Success'),
                    'message': _("Invoice approved"),
                    'sticky': False,
                })
            else:
                error_messages = False
                response_message = response.get('message', '')
                if isinstance(response_message, dict):
                    error_messages = parse_error_message(response_message)
                elif isinstance(response_message, list):
                    error_messages = []
                    for message in response_message:
                        error_messages += parse_error_message(message)

                if error_messages:
                    msg = "\n".join(error_messages)
                else:
                    msg = _("check log.")
                action['params']['message'] = msg
        else:
            action['params']['message'] = response + ', check logs for more details'

        return action

    def prepare_invoice_details(self):
        self.ensure_one()
        if not self.id:
            raise UserError(_(
                "Save Invoice before Getting confirmation number."
            ))
        if not self.invoice_date:
            raise UserError(_(
                f"You cannot get confirmation number without setting the confirmation date. ({self.name})"
            ))
        if not self.partner_id or not self.partner_id.name:
            raise UserError(_("The field 'Customer' is required, please complete it to validate the Customer Invoice."))

        values = {
            "invoice_id": str(self.id)[:50],
            "invoice_type": GET_MOVE_TYPE_NUMBER.get(self.move_type),
            "vat_number": int(self.env.company.vat),
            # "union_vat_number": 125847553,
            "authorized_company": CONSTS.get('manufacturer_license_num'),
            "user_name": self.env.user.login[:25],
            "customer_name": self.partner_id.name[:25] if self.partner_id.name else "",
            "invoice_date": self.invoice_date.strftime('%Y-%m-%d') if self.invoice_date else "",
            "invoice_issuance_date": self.date.strftime('%Y-%m-%d') if self.date else "",
            # "branch_id": "533",
            "accounting_software_number": CONSTS.get('software_registry_num'),
            # "client_software_key": "76857",
            "amount_before_discount": round(self.amount_untaxed, 2),
            "discount": 0.00,
            "payment_amount": round(abs(self.amount_untaxed_signed), 2),  # Ticket : HT02170
            "vat_amount": round(abs(self.amount_tax_signed), 2),  # Ticket : HT02170
            "payment_amount_including_vat": round(abs(self.amount_total_signed), 2),  # Ticket : HT02170
            # "invoice_note": "הערות",
            # "Action": 0,
            # TODO check when this needs to change? "סימון 3 אם נבחר היפוך חיוב, סכום מע"מ חייב להיות 0. סימון 4 - חשבון עסקה / פרופורמה."
            # "vehicle_license_number": 584752145,
            # "phone_of_driver": "0505674235",
            # "arrival_date": "2023-02-26",
            # "estimated_arrival_time": "13:25",
            # "transition_location": 12,
            # "delivery_address": "כתובת אספקה",
            # "additional_information": 0,
        }
        if self.state == 'posted':
            values['invoice_reference_number'] = self.name[:20] if self.name else ''
        if self.partner_id.commercial_partner_id.vat:
            values['customer_vat_number'] = int(self.partner_id.commercial_partner_id.vat)
        return values

    def verify_bill_conf_number(self):
        self.ensure_one()
        if not self.rt_confirmation_number:
            raise UserError(_(
                "You cannot get document details without a confirmation number."
            ))
        endpoint = 'invoice-information/v1/details'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {token}'.format(token=self.env.company.rt_taxes_access_token),
        }
        values = {
            "Customer_VAT_Number": int(self.env.company.vat),
            "Confirmation_Number": self.rt_confirmation_number
        }
        if self.partner_id.commercial_partner_id.vat:
            values["Vat_Number"] = int(self.partner_id.commercial_partner_id.vat)
        status, response = self._do_request(endpoint, params=values, headers=headers, method='POST', type='invoice',
                                            need_json_dump=True)

        action = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'danger',
                'title': _('Failure'),
                'message': 'Failed to Receive Details, check log.',
                'sticky': True,  # True/False will display for few seconds if false
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
        if status == 200:
            # TODO: this endpoint doesn't have detailed example of unsuccessful status 200
            response_message = response.get('Message', '')
            if isinstance(response_message, dict) and not response_message.get('error'):
                # call wizard
                # mark doc as approved if response is correct
                wizard = self.env['oii.invoice.details.wizard'].create({
                    "invoice_type": response_message.get('Invoice_Type'),
                    "vat_number": response_message.get('Vat_Number'),
                    "reference_number": response_message.get('Invoice_Reference_Number'),
                    "customer_vat_number": response_message.get('Customer_VAT_Number'),
                    "customer_name": response_message.get('Customer_Name'),
                    "invoice_date": response_message.get('Invoice_Date'),
                    "invoice_issuance_date": response_message.get('Invoice_Issuance_Date'),
                    "amount_untaxed": response_message.get('Payment_Amount'),
                    "amount_tax": response_message.get('VAT_Amount'),
                    "amount_total": response_message.get('Payment_Amount_Including_VAT'),
                })

                action = {
                    'type': 'ir.actions.act_window',
                    'name': _('Document Details'),
                    'res_model': 'oii.invoice.details.wizard',
                    'view_mode': 'form',
                    'target': 'new',
                    'res_id': wizard.id,
                    'view_id': self.env.ref("oii_israel_invoices.oii_invoice_details_wizard_form_view", False).id,
                }

            elif isinstance(response_message, str):
                action['params']['message'] = response_message
        else:
            action['params']['message'] = response + ', check logs for more details'

        return action
