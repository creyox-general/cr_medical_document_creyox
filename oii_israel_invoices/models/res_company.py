
from odoo import fields, models, api
class ResCompany(models.Model):
    _inherit = 'res.company'

    enable_taxes_integration = fields.Boolean("Enable Integration", default=False)
    rt_taxes_host = fields.Char("Taxes Base URL", default='https://openapi.taxes.gov.il/shaam/tsandbox/')
    rt_taxes_access_token = fields.Char("Access Token")
    rt_taxes_refresh_token = fields.Char("Refresh Token")
    rt_taxes_minimum_untaxed_amount = fields.Integer("Minimum Untaxed Amount", default=25000)
    rt_client_id = fields.Char("Client Id")
    rt_client_secret = fields.Char("Client Secret Key")
