from logging import exception
from odoo.addons.whatsapp.tools.whatsapp_exception import WhatsAppError
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import secrets
import json
import string
from datetime import datetime

class WhatsappTemplate(models.Model):
    _inherit = "whatsapp.template"

    template_category = fields.Selection(
        [("template", "Template"), ("interactive", "Interactive")],
        string="Template Type",
    )

    wa_interactive_ids = fields.One2many(
        comodel_name="wa.interactive.template",
        inverse_name="wa_template_id",
        string="Interactive",
    )
    otp_length = fields.Integer('OTP length', default=6)
    otp_expiration_time = fields.Integer('OTP Expiration Time', default=5)

    partner_id = fields.Many2one('res.partner', string="Contact")

    @api.constrains('otp_expiration_time')
    def _check_otp_expiration_time(self):
        for record in self:
            if record.otp_expiration_time > 10:
                raise ValidationError('The OTP expiration time must be less than or equals to 10')

    @api.constrains('otp_length')
    def _check_otp_length(self):
        for record in self:
            if record.otp_length > 6 or record.otp_length < 4:
                raise ValidationError('The OTP length must be less than or equal to 6 and greater than or equals to 4.')

    def button_set_status_to_added(self):
        for rec in self:
            rec.status = "approved"

    def generate_secure_otp(self, length):
        characters = string.digits  # Only digits for OTP
        otp = ''.join(secrets.choice(characters) for _ in range(length))
        return otp

    def _get_interactive_component(self):
        params = []
        for interactive in self.wa_interactive_ids:
            template_dict = {}
            template_dict.update({"type": interactive.interactive_type})
            if self.header_type == "text":
                header = {"type": self.header_type, "text": self.header_text}
                template_dict.update({"header": header})
            elif self.header_type in ["image", "video", "document"]:
                attachment = self.header_attachment_ids
                header = [
                    self.env["whatsapp.message"]._prepare_attachment_vals(
                        attachment, wa_account_id=self.wa_account_id
                    )
                ]
                # if self.header_type == 'document':
                #     header[0].get(self.header_type).update({'filename': attachment.name})
                template_dict.update({"header": header[0]})
            if self.body:
                body = {"text": self.body}
                template_dict.update({"body": body})
            if self.footer_text:
                footer = {"text": self.footer_text}
                template_dict.update({"footer": footer})
            if interactive.interactive_type == "product_list":
                if interactive.interactive_product_list_ids:
                    section = []
                    for product in interactive.interactive_product_list_ids:
                        product_items = []

                        for products in product.product_list_ids:
                            product_item = {
                                "product_retailer_id": products.product_retailer_id
                            }

                            product_items.append(product_item)

                        section.append(
                            {
                                "title": product.main_title,
                                "product_items": product_items,
                            }
                        )

                    action = {"catalog_id": interactive.catalog_id, "sections": section}

                    template_dict.update({"action": action})

            elif interactive.interactive_type == "button":
                if interactive.interactive_button_ids:
                    buttons = []
                    for btn_id in interactive.interactive_button_ids:
                        buttons.append(
                            {
                                "type": "reply",
                                "reply": {"id": btn_id.id, "title": btn_id.title},
                            }
                        )
                    action = {"buttons": buttons}

                    template_dict.update({"action": action})

            elif interactive.interactive_type == "list":
                if interactive.interactive_list_ids:
                    section = []
                    for list_id in interactive.interactive_list_ids:
                        rows = []
                        for lists in list_id.title_ids:
                            title_ids = {
                                "id": lists.id,
                                "title": lists.title,
                                "description": lists.description or "",
                            }
                            rows.append(title_ids)

                        section.append({"title": list_id.main_title, "rows": rows})
                    action = {"button": list_id.main_title, "sections": section}
                    template_dict.update({"action": action})

            elif interactive.interactive_type == "product":
                action = {
                    "catalog_id": interactive.catalog_id,
                    "product_retailer_id": interactive.product_retailer_id,
                }
                template_dict.update({"action": action})

            if bool(template_dict):
                params.append(template_dict)
        return params

    def _get_send_template_vals(self, record, whatsapp_message):
        temp_vals = {}
        attachment = {}
        if self.template_type == 'authentication' and self.model_id.model == 'res.partner':
            otp = self.generate_secure_otp(self.otp_length)
            record.sudo().write({
                'otp_text': otp,
                'otp_time': datetime.now(),
            })
        if self.template_category == "interactive":
            interactive = self._get_interactive_component()
            if interactive:
                temp_vals.update(interactive[0])
            return temp_vals, attachment
        else:
            return super(WhatsappTemplate, self)._get_send_template_vals(record, whatsapp_message)

    def button_submit_template(self):
        if self.template_type == 'authentication':
            components = []
            if self.body:
                body_component = {"type": "BODY", "add_security_recommendation": True}
                components.append(body_component)
            if self.otp_expiration_time:
                footer_component = {"type": "FOOTER", "code_expiration_minutes": self.otp_expiration_time}
                components.append(footer_component)
            if self.button_ids.filtered(lambda button: button.button_type == 'url' and button.url_type == 'dynamic'):
                for button in self.button_ids:
                    button_component = {"type": "BUTTONS", "buttons": [{"type": "OTP", "otp_type": "COPY_CODE"}]}
                    components.append(button_component)
            json_data = json.dumps({
                'name': self.template_name,
                'languages': self.lang_code,
                'category': self.template_type.upper(),
                'components': components,
            })
            try:
                response = self.wa_account_id._api_requests_ext("POST", f"/{self.wa_account_id.account_uid}/upsert_message_templates",
                                               auth_type="bearer", headers={'Content-Type': 'application/json'},
                                               data=json_data)
                response_json = response.json()
                if response_json.get('data')[0].get('id'):
                    self.sudo().write({
                        'id':response_json.get('data')[0].get('id'),
                        'status': response_json.get('data')[0].get('status').lower()
                    })
            except Exception as e:
                raise UserError(e)
        else:
            return super().button_submit_template()


    @api.constrains("wa_interactive_ids")
    def _check_wa_interactive_ids(self):
        if len(self.wa_interactive_ids) > 1:
            raise UserError(
                _(
                    "Adding more than one interactive type in a template is not supported. Please revise the template accordingly."
                )
            )
        else:
            pass

    def send_pre_message_by_whatsapp(self):
        partner_id = self.env.context.get('partner', False)
        if partner_id:
            partner = self.env['res.partner'].sudo().search([('id', '=', partner_id)])
            wizard_rec = self.env['whatsapp.composer'].with_context(active_model=self.model_id.model,
                                                                    active_id=partner_id).create(
                {'phone': partner.mobile or partner.phone, "res_model": self.model_id.model,
                 'wa_template_id': self.id})
            wizard_rec._send_whatsapp_template()
