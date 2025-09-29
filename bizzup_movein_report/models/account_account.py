# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountAccount(models.Model):
    """Inherited AccountAccount for new fields."""
    _inherit = 'account.account'

    external_software_code = fields.Integer("External Software Code",
                                            copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        """Inherited Create function for external_software_code > 8
        Validation"""
        res = super(AccountAccount, self).create(vals_list)
        for rec in res:
            external_software_code = str(rec.external_software_code)
            if len(external_software_code) > 8:
                raise ValidationError(
                    _("You cannot enter more than 8 digits in External Software Code."))
        return res

    def write(self, vals):
        """Inherited Write function for external_software_code > 8
                Validation"""
        res = super(AccountAccount, self).write(vals)
        external_software_code = str(vals.get('external_software_code'))
        if len(external_software_code) > 8:
            raise ValidationError(
                _("You cannot enter more than 8 digits in External Software Code."))
        return res
