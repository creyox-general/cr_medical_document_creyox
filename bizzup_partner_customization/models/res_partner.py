from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    """Class inherited to add withholding information at partner."""
    _inherit = "res.partner"

    bizzup_partner_id = fields.Char("Bizzup Partner ID")
    
    @api.constrains('bizzup_partner_id')
    def _constrains_bizzup_partner_id(self):
        for rec in self:
            if rec.bizzup_partner_id and len(rec.bizzup_partner_id) > 9:
                raise UserError(_('Length must be 9 or less'))
