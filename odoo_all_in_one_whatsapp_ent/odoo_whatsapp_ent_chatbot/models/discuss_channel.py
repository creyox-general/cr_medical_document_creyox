# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.
import random

from odoo import api, fields, models, tools


class ChatbotDiscussChannel(models.Model):
    _inherit = "discuss.channel"

    wa_chatbot_id = fields.Many2one(
        comodel_name="whatsapp.chatbot", string="Whatsapp Chatbot"
    )
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        domain=lambda self: [
            ("wa_chatbot_id", "!=", False),
            ("wa_chatbot_id", "=", self.wa_chatbot_id.id),
        ],
        string="Messages",
    )
    script_sequence = fields.Integer(string="Sequence", default=1)
    is_chatbot_ended = fields.Boolean(string="Inactivate Chatbot")

    def chatbot_activate(self):
        channels = self.search([])
        for rec in channels:
            if rec.is_chatbot_ended:
                rec.is_chatbot_ended = False
                rec.wa_chatbot_id = rec.wa_account_id.wa_chatbot_id.id

    def _notify_thread(self, message, msg_vals=False, **kwargs):
        res = super(ChatbotDiscussChannel, self)._notify_thread(
            message, msg_vals=msg_vals, **kwargs
        )
        if self.env.context.get('stop_recur'):
            return res
        if message:
            wa_account_id = self.wa_account_id
            user_partner = (
                wa_account_id.notify_user_ids and wa_account_id.notify_user_ids[0] or []
            )
            mail_message_id = message
            partner_id = mail_message_id.author_id
            if wa_account_id and user_partner and wa_account_id.wa_chatbot_id and self:
                message.update({"wa_chatbot_id": wa_account_id.wa_chatbot_id.id})
                if not self.is_chatbot_ended:
                    message_script = (
                        self.env["whatsapp.chatbot"]
                        .search([("id", "=", wa_account_id.wa_chatbot_id.id)])
                        .mapped("step_type_ids")
                        .filtered(
                            lambda l: l.message
                            == tools.html2plaintext(mail_message_id.body)
                        )
                    )

                    current__chat_seq_script = (
                        self.env["whatsapp.chatbot"]
                        .search([("id", "=", wa_account_id.wa_chatbot_id.id)])
                        .mapped("step_type_ids")
                        .filtered(lambda l: l.sequence == self.script_sequence)
                    )
                    if message_script:
                        chatbot_script_lines = message_script
                    elif current__chat_seq_script and current__chat_seq_script.step_call_type != 'action':
                        chatbot_script_lines = current__chat_seq_script
                    else:
                        chatbot_script_lines = wa_account_id.wa_chatbot_id.step_type_ids[0]

                    for chat in chatbot_script_lines:
                        if chat.sequence >= self.script_sequence:
                            self.write(
                                {
                                    "wa_chatbot_id": chat.whatsapp_chatbot_id.id
                                    if wa_account_id.wa_chatbot_id
                                    == chat.whatsapp_chatbot_id
                                    else False,
                                    "script_sequence": chat.sequence,
                                }
                            )
                        elif (
                            current__chat_seq_script
                            and current__chat_seq_script.parent_id
                            and current__chat_seq_script.parent_id == chat.parent_id
                        ):
                            self.write(
                                {
                                    "wa_chatbot_id": chat.whatsapp_chatbot_id.id,
                                    "script_sequence": chat.sequence,
                                }
                            )
                        else:
                            first_script = (
                                self.env["whatsapp.chatbot"]
                                .search([("id", "=", self.wa_chatbot_id.id)])
                                .mapped("step_type_ids")
                                .filtered(lambda l: l.sequence == 1)
                            )
                            if first_script:
                                self.write(
                                    {
                                        "wa_chatbot_id": chat.whatsapp_chatbot_id.id,
                                        "script_sequence": first_script.sequence,
                                    }
                                )
                            else:
                                self.write(
                                    {
                                        "wa_chatbot_id": chat.whatsapp_chatbot_id.id if wa_account_id and wa_account_id.wa_chatbot_id == chat.whatsapp_chatbot_id
                                        else False,
                                        "script_sequence": chat.sequence,
                                    })

                        if chat.step_call_type in ["template", "interactive"]:
                            template = chat.template_id
                            if template:
                                whatsapp_composer = (
                                    self.env["whatsapp.composer"]
                                    .with_user(user_partner.id)
                                    .with_context(
                                        {
                                            "active_id": partner_id.id,
                                            "is_chatbot": True,
                                            "wa_chatbot_id": self.wa_chatbot_id.id,
                                        }
                                    )
                                    .create(
                                        {
                                            "phone": partner_id.mobile,
                                            "wa_template_id": template.id,
                                            "res_model": template.model_id.model,
                                        }
                                    )
                                )
                                whatsapp_composer.with_context({'stop_recur': True})._send_whatsapp_template()

                        elif chat.step_call_type == "message":
                            self.with_context({'stop_recur': True}).with_user(user_partner.id).message_post(
                                body=chat.answer,
                                message_type="whatsapp_message",
                            )
                        elif chat.step_call_type == "action":
                            if chat.action_id.binding_model_id.model == "crm.lead":
                                lead_message = (
                                    "Dear "
                                    + partner_id.name
                                    + ", We are pleased to inform you that your lead has been successfully generated. Our team will be in touch with you shortly."
                                )
                                self.with_context({'stop_recur': True}).with_user(user_partner.id).message_post(
                                    body=lead_message, message_type="whatsapp_message"
                                )
                                self.env["crm.lead"].with_user(
                                    user_partner.id
                                ).sudo().create(
                                    {
                                        "name": partner_id.name + " WA ChatBot Lead ",
                                        "partner_id": partner_id.id,
                                        "email_from": partner_id.email
                                        if partner_id.email
                                        else False,
                                        "mobile": partner_id.mobile,
                                        "user_id": user_partner.id,
                                        "type": "lead",
                                        "description": "Lead created by Chatbot for customer "
                                        + partner_id.name,
                                    }
                                )
                            if (
                                chat.action_id.binding_model_id.model
                                == "helpdesk.ticket"
                            ):
                                ticket_message = (
                                    "Dear "
                                    + partner_id.name
                                    + ", We are pleased to inform you that your Ticket has been raised. Our team will be in touch with you shortly."
                                )
                                self.with_context({'stop_recur': True}).with_user(user_partner.id).message_post(
                                    body=ticket_message, message_type="whatsapp_message"
                                )
                                self.env["helpdesk.ticket"].with_user(
                                    user_partner.id
                                ).sudo().create(
                                    {
                                        "name": partner_id.name + " WA ChatBot Ticket ",
                                        "partner_id": partner_id.id,
                                        "partner_phone": partner_id.mobile,
                                        "user_id": user_partner.id,
                                        "description": "Ticket raised by Chatbot for customer "
                                        + partner_id.name,
                                    }
                                )
                            if (
                                chat.action_id.binding_model_id.model
                                == "discuss.channel"
                            ):
                                available_operator = False
                                active_operator = wa_account_id.wa_chatbot_id.mapped(
                                    "user_ids"
                                ).filtered(lambda user: user.im_status == "online")
                                if active_operator:
                                    wa_chatbot_channels = (
                                        wa_account_id.wa_chatbot_id.mapped(
                                            "channel_ids"
                                        )
                                    )
                                    for wa_channel in wa_chatbot_channels:
                                        operators = active_operator.filtered(
                                            lambda av_user: av_user.partner_id
                                            not in wa_channel.channel_member_ids.partner_id
                                        )
                                        if operators:
                                            for operator in operators:
                                                available_operator = operator.partner_id
                                        else:
                                            available_operator = random.choice(active_operator).partner_id
                                    if available_operator:
                                        added_operator = (
                                            self.channel_partner_ids.filtered(
                                                lambda x: x.id == available_operator.id
                                            )
                                        )
                                        if added_operator:
                                            self.write(
                                                {
                                                    "is_chatbot_ended": True,
                                                    "wa_chatbot_id": False,
                                                }
                                            )
                                        else:
                                            self.write(
                                                {
                                                    "channel_partner_ids": [
                                                        (4, available_operator.id)
                                                    ],
                                                    "is_chatbot_ended": True,
                                                    "wa_chatbot_id": False,
                                                }
                                            )
                                        mail_channel_partner = (
                                            self.env["discuss.channel.member"]
                                            .sudo()
                                            .search(
                                                [
                                                    ("channel_id", "=", self.id),
                                                    (
                                                        "partner_id",
                                                        "=",
                                                        available_operator.id,
                                                    ),
                                                ]
                                            )
                                        )
                                        mail_channel_partner.write({"is_pinned": True})
                                        wait_message = "We are connecting you with one of our experts. Please wait a moment."
                                        self.with_context({'stop_recur': True}).with_user(user_partner.id).message_post(
                                            body=wait_message,
                                            message_type="whatsapp_message",
                                        )
                                        user_message = (
                                            "You are now chatting with "
                                            + available_operator.name
                                        )
                                        self.with_context({'stop_recur': True}).with_user(user_partner.id).message_post(
                                            body=user_message,
                                            message_type="whatsapp_message",
                                        )
                                else:
                                    no_user_message = "Apologies, but there are currently no active operators available."
                                    self.with_context({'stop_recur': True}).with_user(user_partner.id).message_post(
                                        body=no_user_message,
                                        message_type="whatsapp_message",
                                    )
                                    user_message = (
                                        "We will connect you with one shortly."
                                    )
                                    self.with_context({'stop_recur': True}).with_user(user_partner.id).message_post(
                                        body=user_message,
                                        message_type="whatsapp_message",
                                    )

        return res


class ChatbotMailMessage(models.Model):
    _inherit = "mail.message"

    wa_chatbot_id = fields.Many2one(
        comodel_name="whatsapp.chatbot", string="Whatsapp Chatbot"
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if self._context.get("wa_chatbot_id"):
                whatsapp_chatbot = self.env["whatsapp.chatbot"].search(
                    [("id", "=", self._context.get("wa_chatbot_id"))]
                )
                if whatsapp_chatbot:
                    vals.update(
                        {
                            "wa_chatbot_id": whatsapp_chatbot.id,
                        }
                    )
        return super(ChatbotMailMessage, self).create(vals_list)
