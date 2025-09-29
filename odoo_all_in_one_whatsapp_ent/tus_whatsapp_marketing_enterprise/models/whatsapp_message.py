from odoo import api, fields, models


class WhatsappMessage(models.Model):
    _inherit = "whatsapp.message"

    whatsapp_messaging_id = fields.Many2one("whatsapp.messaging")

    @api.model_create_multi
    def create(self, vals):
        messages = super(WhatsappMessage, self).create(vals)
        for message in messages:
            whatsapp_messaging = (
                self.env["whatsapp.messaging"].search(
                    [("id", "=", self._context.get("whatsapp_messaging_id"))]
                )
                if self._context.get("whatsapp_messaging_id")
                else self.env["whatsapp.messaging"]
            )
            if whatsapp_messaging:
                message.update({"whatsapp_messaging_id": whatsapp_messaging.id})
                return message
            else:
                return message
