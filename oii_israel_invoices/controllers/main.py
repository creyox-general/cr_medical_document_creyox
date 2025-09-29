import logging
import pprint

from odoo import http
from odoo.http import request


_logger = logging.getLogger(__name__)


class OiiTaxesController(http.Controller):
    _callback_url = '/oii/callback'

    @http.route(_callback_url, type='http', methods=['GET', 'POST'], auth='public', csrf=False)
    def oii_callback_webhook(self):
        data = request.get_json_data()
        _logger.info("Callback from Taxes with data:\n%s", pprint.pformat(data))
        return request.make_json_response('')