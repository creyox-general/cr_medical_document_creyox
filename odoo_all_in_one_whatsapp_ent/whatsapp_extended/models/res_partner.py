from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    otp_text = fields.Char(string="OTP Text")
    otp_time = fields.Datetime(string='OTP Time')
    wa_message_count = fields.Integer(string="WhatsApp Message Count",
                                   compute='compute_wa_message_count',
                                   default=0)

    def compute_wa_message_count(self):
        for record in self:
            record.wa_message_count = self.env['whatsapp.message'].search_count(
                ['|', ('mobile_number', '=', self.mobile), ('mobile_number', '=', self.phone)])

