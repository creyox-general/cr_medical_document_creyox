from odoo import models, fields, api, tools
from datetime import datetime


class TestWhatsappMarketing(models.TransientModel):
    _name = 'test.whatsapp.marketing'
    _description = 'Test for marketing campaigns'

    messaging_type = fields.Selection([('contact', 'Contact'),
                                       ('message_list', 'Message List')])
    message_list_contact_id = fields.Many2one('whatsapp.messaging.lists.contacts', 'Message List Contact')
    partner_id = fields.Many2one('res.partner')
    template_id = fields.Many2one('whatsapp.template')
    body_html = fields.Html('Body')

    def test_whatsapp_marketing(self):
        for record in self:
            active_id = False
            phone = False
            if record.messaging_type == 'contact':
                active_id = record.partner_id
                phone = record.partner_id.mobile
            if record.messaging_type == 'message_list':
                active_id = record.message_list_contact_id
                phone = record.message_list_contact_id.phone
            if active_id and phone:
                whatsapp_composer = self.env["whatsapp.composer"].with_context({"active_id": active_id.id}).create({
                            "phone": phone,
                            "wa_template_id": record.template_id.id,
                            "res_model": record.template_id.model_id.model,
                        })
                whatsapp_composer._send_whatsapp_template()
            return {'effect': {'fadeout': 'slow',
                               'message': "Whatsapp Template Sent Successfully",
                               }
                    }
