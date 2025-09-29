import base64
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class BaseAutomation(models.Model):
    _inherit = 'base.automation'

    is_whatsapp_action = fields.Boolean(string='Is_whatsapp_action', required=False)

    @api.onchange('action_server_ids')
    def _onchange_get_whatsapp_actions(self):
        for val in self:
            val.is_whatsapp_action = bool(val.action_server_ids.filtered(lambda x: x.wa_template_id))


class ServerActions(models.Model):
    """ Add SMS option in server actions. """
    _name = 'ir.actions.server'
    _inherit = ['ir.actions.server']

    state = fields.Selection(selection_add=[
        ("whatsapp", "Send Whatsapp Message"),
    ], ondelete={"whatsapp": "cascade"})

    isWaMsgs = fields.Boolean(default=False)

    wa_template_id = fields.Many2one(
        'whatsapp.template', 'WA Template', ondelete='set null',
        domain="[('model_id', '=', model_id)]",
    )

    def _run_action_whatsapp_multi(self, eval_context=None):
        # TDE CLEANME: when going to new api with server action, remove action
        if not self.wa_template_id or self._is_recompute():
            return False

        records = eval_context.get('records') or eval_context.get('record')
        if not records:
            return False

        user_partner = self.wa_template_id.wa_account_id.notify_user_ids and self.wa_template_id.wa_account_id.notify_user_ids[0] or []

        for rec in records:
            if rec._name == 'res.partner' and user_partner:
                whatsapp_composer = self.env['whatsapp.composer'].with_user(
                    user_partner.id).create(
                    {
                        'phone': rec.mobile,
                        'wa_template_id': self.wa_template_id.id,
                        'res_model': rec._name,
                    }
                )
                whatsapp_composer._send_whatsapp_template()

            else:
                if rec.partner_id and user_partner:
                    whatsapp_composer = self.env['whatsapp.composer'].with_user(
                        user_partner.id).create(
                        {
                            'phone': rec.partner_id.mobile,
                            'wa_template_id': self.wa_template_id.id,
                            'res_model': rec._name,
                        }
                    )
                    whatsapp_composer._send_whatsapp_template()
        return False
