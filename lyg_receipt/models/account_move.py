#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################
from odoo import fields, models, api, _

import logging

_logger = logging.getLogger(__name__)
tax_value = 0.0
MAX_HASH_VERSION = 4

class AccountMove(models.Model):
    _inherit = 'account.move'

    code = fields.Char(related='company_id.account_fiscal_country_id.code',
                       string="Code of Country")

    def _get_integrity_hash_fields(self):
        # Use the latest hash version by default, but keep the old one for backward compatibility when generating the integrity report.
        hash_version = self._context.get('hash_version', MAX_HASH_VERSION)
        if hash_version == 1:
            return ['date', 'journal_id', 'company_id']
        elif hash_version in (2, 3, 4):
            return ['name', 'company_id']
        raise NotImplementedError(f"hash_version={hash_version} doesn't exist")

    def action_invoice_create_receipt(self):
        for sale in self:
            if sale.partner_id:
                sale_receipt_id = self.env['lyg.account.receipt'].create({'partner_id': sale.partner_id.id})
                return self.action_show_invoice_receipt(sale_receipt_id)

    def action_show_invoice_receipt(self, sale_receipt_id):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'lyg.account.receipt',
            'res_id': sale_receipt_id.id,
            'view_id': self.env.ref('lyg_receipt.view_account_receipt_form').id,
            'target': 'current',
        }

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        """Apply partner filter from context if receipt_invoice_filter is set."""
        context = self._context
        partner_id = context.get('lyg_receipt_partner_id')

        if context.get('receipt_invoice_filter') and partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            partner_ids = [partner.id]
            if partner.parent_id:
                partner_ids.append(partner.parent_id.id)
            domain += [('partner_id', 'in', partner_ids)]

        return super()._search(domain, offset=offset, limit=limit, order=order)
