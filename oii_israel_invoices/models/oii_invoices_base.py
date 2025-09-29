import json
import logging
import requests
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.modules.registry import Registry


_logger = logging.getLogger(__name__)

TIMEOUT = 20


class OiiInvoicesBase(models.AbstractModel):
    _name = 'oii.invoices.base'
    _description = 'Israel Invoices Integration Engine'

    @api.model
    def _do_request(self, endpoint, params=None, headers=None, method='POST', url=None, timeout=TIMEOUT, type='',
                    need_json_dump=False):
        """ Execute the request to Israel Taxes API. Return a tuple ('HTTP_CODE', 'HTTP_RESPONSE')
            :param endpoint : the endpoint to contact
            :param params : dict or already encoded parameters for the request to make
            :param headers : headers of request
            :param method : the method to use to make the request
            :param url : the url to contact.
        """
        company = self.env.company
        if not company.enable_taxes_integration:
            raise UserError("Taxes Integration Disabled!")
        if params is None:
            params = {}
        if headers is None:
            headers = {}
        if url is None:
            url = self.env.company.rt_taxes_host

        full_url = url + endpoint
        log_vals = {
            'request_body': dict(params),
            'end_point': full_url,
            'headers': headers,
            'type': type,
            'state': 'fail',
            'method': method.lower()
        }
        if self.id:
            log_vals.update({
                'parent_res_model': self._name,
                'parent_res_id': self.id,
            })
        if need_json_dump:
            params = json.dumps(params)

        res = response = status = None
        try:
            if method.upper() in ('GET', 'DELETE'):
                res = requests.request(method.lower(), full_url, params=params, timeout=timeout)
            elif method.upper() in ('POST', 'PATCH', 'PUT'):
                res = requests.request(method.lower(), full_url, data=params, headers=headers, timeout=timeout)
            else:
                raise Exception(_('Method not supported [%s] not in [GET, POST, PUT, PATCH or DELETE]!', method))

            status = res.status_code
            log_vals.update(
                status_code=status,
            )
            res.raise_for_status()
            if status == 200:
                log_vals.update(
                    response=res.json(),
                    state='success',
                    # TODO Is it ok to mark as sucess without checking if response has errors? looking into Message.get(errors)?
                )
                response = res.json()

            self.create_api_logs(log_vals)

        except requests.HTTPError as error:
            log_vals.update(
                response=error.response.text,
                failure_reason=error.response.reason,
            )
            response = error.response.reason
            self.create_api_logs(log_vals)

        except requests.exceptions.Timeout:
            msg = "Timeout: the server did not reply within 60s"
            log_vals['failure_reason'] = msg
            self.create_api_logs(log_vals)
            raise ValidationError(msg)

        except (ValueError, requests.exceptions.ConnectionError):
            msg = "API Server not reachable, please try again later"
            if res and res.text:
                msg = res.text
            log_vals['failure_reason'] = msg
            self.create_api_logs(log_vals)
            raise ValidationError(msg)

        return status, response

    def create_api_logs(self, values):
        with Registry(self._cr.dbname).cursor() as cr:
            self = self.with_env(self.env(cr=cr))
            log = self.env['oii.invoices.logs'].create(values)
            return self.browse(log.id)
