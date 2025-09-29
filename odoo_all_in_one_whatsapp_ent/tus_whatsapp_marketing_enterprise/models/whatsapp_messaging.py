import logging

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

MASS_WHATSAPP_BUSINESS_MODELS = ["res.partner", "whatsapp.messaging.lists"]


class WhatsAppMessaging(models.Model):
    _description = "Whatsapp Messaging"
    _name = "whatsapp.messaging"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "name"

    name = fields.Char("Name", required=True)

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_queue", "In Queue"),
            ("sending", "Sending"),
            ("done", "Sent"),
        ],
        string="Status",
        required=True,
        copy=False,
        default="draft",
    )
    domain = fields.Boolean("Domain")
    partner_ids = fields.Many2many("res.partner", string="Partners")
    whatsapp_messaging_lists_ids = fields.Many2many("whatsapp.messaging.lists")
    wa_messaging_model_id = fields.Many2one(
        "ir.model",
        string="Recipients Model",
        domain=[("model", "in", MASS_WHATSAPP_BUSINESS_MODELS)],
    )
    wa_messaging_domain = fields.Char(string="WA Messaging Domain", default=[])
    body_html = fields.Html("Body", translate=True, sanitize=False)
    schedule_date = fields.Datetime(string="Schedule in the Future")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user
    )

    template_id = fields.Many2one(
        "whatsapp.template",
        "Use template",
        index=True,
        # domain=_get_current_model_template,
    )
    is_partner = fields.Boolean(string="Partner", compute="_compute_partner")
    mail_history_ids = fields.One2many("whatsapp.message", "whatsapp_messaging_id")
    marketing_contact_mes_history_ids = fields.One2many(
        "marketing.contact.history", "marketing_contact_id"
    )

    wa_account_id = fields.Many2one("whatsapp.account", "Provider")

    received_ratio = fields.Integer(
        compute="_compute_statistics", string="Received Ratio"
    )
    inqueue_ratio = fields.Integer(
        compute="_compute_statistics", string="In Queue Ratio"
    )
    sent_ratio = fields.Integer(compute="_compute_statistics", string="Sent Ratio")
    delivered_ratio = fields.Integer(
        compute="_compute_statistics", string="Delivered Ratio"
    )
    read_ratio = fields.Integer(compute="_compute_statistics", string="Read Ratio")
    fail_ratio = fields.Integer(compute="_compute_statistics", string="Fail Ratio")
    cancel_ratio = fields.Integer(compute="_compute_statistics", string="Cancel Ratio")
    is_cron_run = fields.Boolean(string='Cron Run?')

    def _compute_statistics(self):
        for rec in self:
            query = 'select state,count(*) AS count from whatsapp_message  where whatsapp_messaging_id =%d group by state ;' % rec.id
            self.env.cr.execute(query)
            types = self._cr.fetchall()
            received = outgoing = sent = delivered = read = fail = cancel = 0
            for val in types:
                if val[0] == 'received':
                    outgoing += val[1]
                elif val[0] == 'outgoing':
                    received += val[1]
                elif val[0] == 'sent':
                    delivered += val[1]
                elif val[0] == 'read':
                    read += val[1]
                elif val[0] == 'delivered':
                    sent += val[1]
                elif val[0] == 'cancel':
                    cancel += val[1]
                else:
                    fail += val[1]

            total_wa_history = received + outgoing + sent + delivered + read + fail + cancel
            rec.received_ratio = (received / total_wa_history) * 100 if total_wa_history != 0 else 0
            rec.inqueue_ratio = (outgoing / total_wa_history) * 100 if total_wa_history != 0 else 0
            rec.sent_ratio = (sent / total_wa_history) * 100 if total_wa_history != 0 else 0
            rec.delivered_ratio = (delivered / total_wa_history) * 100 if total_wa_history != 0 else 0
            rec.read_ratio = (read / total_wa_history) * 100 if total_wa_history != 0 else 0
            rec.fail_ratio = (fail / total_wa_history) * 100 if total_wa_history != 0 else 0
            rec.cancel_ratio = (cancel / total_wa_history) * 100 if total_wa_history != 0 else 0

    def _action_view_documents_filtered(self, view_filter):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "whatsapp.whatsapp_message_action"
        )
        action["domain"] = [
            ("state", "=", view_filter),
            ("whatsapp_messaging_id", "=", self.id),
        ]
        return action

    def action_view_inqueue(self):
        return self._action_view_documents_filtered("outgoing")

    def action_view_sent(self):
        return self._action_view_documents_filtered("sent")

    def action_view_delivered(self):
        return self._action_view_documents_filtered("delivered")

    def action_view_received(self):
        return self._action_view_documents_filtered("received")

    def action_view_read(self):
        return self._action_view_documents_filtered("read")

    def action_view_fail(self):
        return self._action_view_documents_filtered("error")

    def action_view_cancel(self):
        return self._action_view_documents_filtered("cancel")

    @api.onchange("company_id", "wa_account_id")
    def onchange_company_provider(self):
        self.template_id = False
        return {
            "domain": {
                "template_id": [
                    ("model_id.model", "=", "res.partner"),
                    ("wa_account_id", "=", self.wa_account_id.id),
                ]
            }
        }

    @api.depends("wa_messaging_model_id")
    def _compute_partner(self):
        # simple logic, but you can do much more here
        for rec in self:
            if rec.wa_messaging_model_id.model == "res.partner":
                rec.is_partner = True
            else:
                rec.is_partner = False

    def action_schedule_date(self):
        self.ensure_one()
        action = self.env.ref(
            "odoo_all_in_one_whatsapp_ent.whatsapp_messaging_schedule_date_action"
        ).read()[0]
        action["context"] = dict(
            self.env.context, default_whatsapp_messaging_id=self.id
        )
        return action

    def put_in_queue(self):
        self.write({"state": "in_queue"})

    def cancel_mass_mailing(self):
        self.write({"state": "draft", "schedule_date": False})

    def action_test_whatsapp_marketing(self):
        for record in self:
            return {
                'name': 'Test Whatsapp Marketing',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                "view_type": "form",
                'res_model': 'test.whatsapp.marketing',
                'target': 'new',
                'view_id': self.env.ref('odoo_all_in_one_whatsapp_ent.test_whatsapp_marketing_wizard_form').id,
                'context': {'default_template_id': record.template_id.id,
                            'default_body_html': record.template_id.body},
            }

    @api.onchange("template_id", "whatsapp_messaging_lists_ids")
    def onchange_template_id_wrapper(self):
        self.ensure_one()
        for record in self:
            if record.template_id:
                template_components = (
                    record.template_id.body
                    or record.template_id.header_type
                    or record.template_id.footer_text
                )
                user_error = False
                if (
                    record.template_id
                    and template_components
                    and record.wa_messaging_model_id
                    and record.wa_messaging_model_id.model == "whatsapp.messaging.lists"
                ):
                    if any(
                        record.whatsapp_messaging_lists_ids.filtered(
                            lambda x: x.contact_type == "wa_list_contact"
                        )
                    ) and any(
                        record.whatsapp_messaging_lists_ids.filtered(
                            lambda x: x.contact_type == "base_contact"
                        )
                    ):
                        raise UserError(
                            _(
                                "You Can not select Contact list and Marketing message list at the same time"
                            )
                        )
                    
                    if (any(record.whatsapp_messaging_lists_ids.filtered(lambda x: x.contact_type == "wa_list_contact")) and record.template_id.model_id.model == 'res.partner') or (any(record.whatsapp_messaging_lists_ids.filtered(lambda x: x.contact_type == "base_contact")) and record.template_id.model_id.model == 'whatsapp.messaging.lists.contacts'):
                        raise UserError(
                            _(
                                "You have selected the list of type " + record.whatsapp_messaging_lists_ids[0].contact_type + " and Template model is " + record.template_id.model_id.name + " Please select the correct model template"
                            )
                        )

                record.body_html = tools.html2plaintext(record.template_id.body)
            else:
                record.body_html = ""

    @api.model
    def _process_whatsapp_messaging_queue(self):
        whatsapp_messagings = self.search(
            [
                ("state", "in", ("in_queue", "sending")),
                "|",
                ("schedule_date", "<", fields.Datetime.now()),
                ("schedule_date", "=", False),
                ("is_cron_run", "=", False),
            ]
        )
        for whatsapp_messaging in whatsapp_messagings:
            try:
                sequence = 1
                # Multi Companies and Multi Providers Code Here, We have passed Default Provider for Scheduled Actions
                message_partner = 0
                unique_phones = set()
                if whatsapp_messaging.is_partner or whatsapp_messaging.whatsapp_messaging_lists_ids.filtered(lambda x: x.contact_type == 'base_contact') and whatsapp_messaging.whatsapp_messaging_lists_ids.contact_ids:
                    to_partners = whatsapp_messaging.whatsapp_messaging_lists_ids.mapped('contact_ids').filtered(
                        lambda x: x.mobile and (x.mobile not in unique_phones and not unique_phones.add(x.mobile)))
                    to_partners |= whatsapp_messaging.partner_ids.filtered(
                        lambda x: x.mobile and (x.mobile not in unique_phones and not unique_phones.add(x.mobile)))
                    if whatsapp_messaging.domain and len(whatsapp_messaging.wa_messaging_domain) > 2:
                        to_partners |= to_partners.search(
                            safe_eval(whatsapp_messaging.wa_messaging_domain)).filtered(lambda x: x.mobile and (
                                x.mobile not in unique_phones and not unique_phones.add(x.mobile)))
                    to_partners = to_partners.filtered(
                        lambda x: x.mobile.lower().strip() not in whatsapp_messaging.mail_history_ids.mapped(
                            'mobile_number'))
                    message_partner += len(to_partners)
                    if not len(to_partners):
                        raise ValueError("Not Enough contact to process")

                    if to_partners:
                        for partner in to_partners:
                            try:
                                whatsapp_messaging.write({"state": "sending"})
                                _logger.info("contact Mobile (Whatsapp Number) %s - %s" % (partner.mobile, str(sequence)))
                                sequence += 1
                                if partner.mobile:
                                    whatsapp_composer = (
                                        self.env["whatsapp.composer"]
                                        .with_context(
                                            {
                                                "active_id": partner.id,
                                                "whatsapp_messaging_id": whatsapp_messaging.id,
                                            }
                                        )
                                        .create(
                                            {
                                                "phone": partner.mobile,
                                                "wa_template_id": whatsapp_messaging.template_id.id,
                                                "res_model": partner._name,
                                            }
                                        )
                                    )
                                    whatsapp_composer._send_whatsapp_template()
                                    whatsapp_messaging.write(
                                        {"marketing_contact_mes_history_ids": [(0, 0, {"phone": partner.mobile})]})
                                    self._cr.commit()
                            except Exception as e:
                                _logger.error(f"{e}")
                                continue
                else:
                    to_contacts = whatsapp_messaging.whatsapp_messaging_lists_ids.wa_list_contacts_ids.filtered(
                        lambda x: x.phone and (x.phone not in unique_phones and not unique_phones.add(x.phone)))
                    to_contacts = to_contacts.filtered(
                        lambda x: x.phone not in whatsapp_messaging.mail_history_ids.mapped('mobile_number'))
                    message_partner += len(to_contacts)

                    for contact in to_contacts:
                        if contact.phone:
                            try:
                                _logger.info(
                                    "contact Mobile (Whatsapp Number) %s  -- [%s]" % (contact.phone, str(sequence)))
                                sequence += 1
                                whatsapp_composer = (
                                    self.env["whatsapp.composer"]
                                    .with_context(
                                        {
                                            "active_id": contact.id,
                                            "whatsapp_messaging_id": whatsapp_messaging.id,
                                        }
                                    )
                                    .create(
                                        {
                                            "phone": contact.phone,
                                            "wa_template_id": whatsapp_messaging.template_id.id,
                                            "res_model": whatsapp_messaging.whatsapp_messaging_lists_ids.wa_list_contacts_ids._name,
                                        }
                                    )
                                )
                                whatsapp_composer._send_whatsapp_template()
                                whatsapp_messaging.write(
                                    {"marketing_contact_mes_history_ids": [(0, 0, {"phone": contact.phone})
                                                                           ]})
                                self._cr.commit()
                            except Exception as e:
                                _logger.error(f"{e}")
                                continue

                if message_partner == len(whatsapp_messaging.mail_history_ids):
                    whatsapp_messaging.write({'is_cron_run': True, "state": "done"})
                    self._cr.commit()

            except Exception as ve:
                _logger.error(f"{ve}")
                continue
