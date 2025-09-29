from odoo import fields, models


class WhatsappAccountInherit(models.Model):
    _inherit = "whatsapp.account"

    wa_chatbot_id = fields.Many2one(
        comodel_name="whatsapp.chatbot",
        string="Whatsapp Chatbot",
        readonly=False,
    )

    def _process_messages(self, value):
        if "messages" not in value and value.get("whatsapp_business_api_data", {}).get(
            "messages"
        ):
            value = value["whatsapp_business_api_data"]

        for messages in value.get("messages", []):
            parent_id = False
            channel = False
            sender_name = value.get("contacts", [{}])[0].get("profile", {}).get("name")
            sender_mobile = messages["from"]
            message_type = messages["type"]
            if message_type == "interactive":
                if "context" in messages:
                    parent_whatsapp_message = (
                        self.env["whatsapp.message"]
                        .sudo()
                        .search([("msg_uid", "=", messages["context"].get("id"))])
                    )
                    if parent_whatsapp_message:
                        parent_id = parent_whatsapp_message.mail_message_id
                    if parent_id:
                        channel = (
                            self.env["discuss.channel"]
                            .sudo()
                            .search([("message_ids", "in", parent_id.id)], limit=1)
                        )

                if not channel:
                    channel = self._find_active_channel(
                        sender_mobile, sender_name=sender_name, create_if_not_found=True
                    )
                kwargs = {
                    "message_type": "whatsapp_message",
                    "author_id": channel.whatsapp_partner_id.id,
                    "subtype_xmlid": "mail.mt_comment",
                    "parent_id": parent_id.id if parent_id else None,
                }
                if message_type == "interactive":
                    if messages.get("interactive") and messages.get("interactive").get(
                        "button_reply"
                    ):
                        message = (
                            messages.get("interactive").get("button_reply").get("title")
                        )
                    elif messages.get("interactive") and messages.get(
                        "interactive"
                    ).get("list_reply"):
                        message = (
                            messages.get("interactive").get("list_reply").get("title")
                        )
                    else:
                        message = ""
                    kwargs["body"] = message
                channel.message_post(whatsapp_inbound_msg_uid=messages["id"], **kwargs)
            else:
                return super(WhatsappAccountInherit, self)._process_messages(value)
