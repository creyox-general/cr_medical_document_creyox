import base64
from cryptography.fernet import Fernet
from hashlib import md5
from odoo import _, fields, models, api
import logging

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _name = 'res.config.settings'
    _inherit = ['res.config.settings', 'oii.invoices.base']

    enable_taxes_integration = fields.Boolean(
        related='company_id.enable_taxes_integration',
        readonly=False
    )
    rt_taxes_host = fields.Char(
        related='company_id.rt_taxes_host',
        readonly=False
    )
    rt_taxes_access_token = fields.Char(
        related='company_id.rt_taxes_access_token',
        readonly=False
    )
    rt_taxes_refresh_token = fields.Char(
        related='company_id.rt_taxes_refresh_token',
        readonly=False
    )
    rt_taxes_minimum_untaxed_amount = fields.Integer(
        related='company_id.rt_taxes_minimum_untaxed_amount',
        readonly=False
    )
    rt_client_id = fields.Char(
        related='company_id.rt_client_id',
        readonly=False
    )
    rt_client_secret = fields.Char(
        related='company_id.rt_client_secret',
        readonly=False
    )
    rt_taxes_client_id = fields.Char("Taxes Client_id", config_parameter='rt_taxes_client_id', default='')
    rt_taxes_client_secret = fields.Char("Taxes Client_key", config_parameter='rt_taxes_client_secret', default='')

    def refresh_token(self):
        company_id = self.env.company
        key = md5(company_id.vat.encode()).digest()
        fernet_key_base64 = base64.urlsafe_b64encode(key.ljust(32, b'\0'))
        fernet = Fernet(fernet_key_base64)

        # HT01977
        # Encrypt and store securely in ir.config_parameter
        encrypted_id = fernet.encrypt(company_id.rt_client_id.encode())
        encrypted_secret = fernet.encrypt(company_id.rt_client_secret.encode())

        self.env['ir.config_parameter'].sudo().set_param('rt_taxes_client_id', encrypted_id)
        self.env['ir.config_parameter'].sudo().set_param('rt_taxes_client_secret', encrypted_secret)

        # HT01977
        # Decrypt for request
        decrypted_client_id = fernet.decrypt(encrypted_id).decode()
        decrypted_secret = fernet.decrypt(encrypted_secret).decode()

        # HT01977
        # Prepare request
        endpoint = 'longtimetoken/oauth2/token'
        values = {
            "client_id": decrypted_client_id,
            "scope": "scope",
            "refresh_token": company_id.rt_taxes_refresh_token,
            "grant_type": "refresh_token",
            "client_secret": decrypted_secret,
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        # HT01977
        # Send request using your internal request method
        status, response = self._do_request(endpoint, params=values, headers=headers, method='POST', type='setting')
        _logger.info("\n\n -------status------- ",status)
        _logger.info("\n\n -------response------- ",response)
        action = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
        # HT01977
        _logger.info("\n\n -------status------- ",status)
        _logger.info("\n\n -------response------- ",response)
        if status == 200 and response.get('access_token'):
            _logger.info("\n\n -------status------- ",status)
            _logger.info("\n\n -------response------- ",response)
            company_id.rt_taxes_access_token = response.get('access_token')
            company_id.rt_taxes_refresh_token = response.get('refresh_token')
            action['params'].update({
                'type': 'success',
                'title': _('Success'),
                'message': _("Generated token successfully"),
                'sticky': False,
            })
        else:
            msg = _("Token generation failed, check log.")
            action['params'].update({
                'type': 'danger',
                'title': _('Failure'),
                'message': msg,
                'sticky': True,
            })
            activity_type = self.env.ref('mail.mail_activity_data_todo')
            if activity_type:
                activity_data = {
                    'activity_type_id': activity_type.id,
                    'res_id': self.env.ref('base.user_admin').partner_id.id,
                    'res_model_id': self.env.ref('base.model_res_partner').id,
                    'date_deadline': fields.Date.today(),
                    'user_id': self.env.ref('base.user_admin').id,
                    'note': msg,
                }
                self.env['mail.activity'].create(activity_data)

        return action
