from odoo import fields, models,_


class ResPartner(models.Model):
    _inherit = "res.partner"

    instagram_account_id = fields.Char("Instagram ID")
    messenger_account_id = fields.Char("Messenger ID")
    messenger_channel_provider_line_ids = fields.One2many(
        "messenger.channel.provider.line",
        "partner_id",
        "Messenger Channel Provider Line",
    )
    facebook_message_count = fields.Integer(string="Facebook Message Count",
                                      compute='compute_facebook_message_count',
                                      default=0)
    instagram_message_count = fields.Integer(string="Instagram Message Count",
                                            compute='compute_instagram_message_count',
                                            default=0)

    def compute_facebook_message_count(self):
        partner_facebook_channel_counts = {partner.id: 0 for partner in self}
        facebook_member_count = self.env['discuss.channel.member']._read_group(
        domain=[
            ('channel_id.channel_type', '=', 'FbChannels'),
            ('partner_id', 'in', self.ids)
        ],
        groupby=['partner_id'],
        aggregates=['id:count'],
    )
        for partner, count in facebook_member_count:
            partner_facebook_channel_counts[partner.id] += count
        for partner in self:
            partner.facebook_message_count = partner_facebook_channel_counts[partner.id]
    def compute_instagram_message_count(self):
        partner_facebook_channel_counts = {partner.id: 0 for partner in self}
        facebook_member_count = self.env['discuss.channel.member']._read_group(
            domain=[
                ('channel_id.channel_type', '=', 'InstaChannels'),
                ('partner_id', 'in', self.ids)
            ],
            groupby=['partner_id'],
            aggregates=['id:count'],
        )
        for partner, count in facebook_member_count:
            partner_facebook_channel_counts[partner.id] += count
        for partner in self:
            partner.instagram_message_count = partner_facebook_channel_counts[partner.id]


    def action_open_partner_fb_channels(self):
        return {
            'name': _('Facebook Chats'),
            'type': 'ir.actions.act_window',
            'domain': [('channel_type','in', ['FbChannels']), ('channel_partner_ids', 'in', self.ids)],
            'res_model': 'discuss.channel',
            'views': [(self.env.ref('whatsapp.discuss_channel_view_list_whatsapp').id, 'list')],
        }
    def action_open_partner_insta_channels(self):
        return {
            'name': _('InstaGram Chats'),
            'type': 'ir.actions.act_window',
            'domain': [('channel_type','in', ['InstaChannels']), ('channel_partner_ids', 'in', self.ids)],
            'res_model': 'discuss.channel',
            'views': [(self.env.ref('whatsapp.discuss_channel_view_list_whatsapp').id, 'list')],
        }