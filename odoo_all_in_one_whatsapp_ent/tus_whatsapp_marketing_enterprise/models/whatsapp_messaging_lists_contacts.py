from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class WhatsAppMessagingListsContacts(models.Model):
    _description = "Whatsapp Messaging List Contacts"
    _name = "whatsapp.messaging.lists.contacts"
    _rec_name = "phone"

    name = fields.Char("Contact Name")
    phone = fields.Char("WhatsApp Number")

    @api.constrains("phone")
    def _verify_phone_number(self):
        for rec in self:
            if rec.phone and not rec.phone.isdigit():
                raise ValidationError(
                    _("The Phone Number must be a sequence of digits.")
                )
