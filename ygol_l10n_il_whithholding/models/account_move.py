#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, \
    AccessError
from odoo.tools import float_compare, float_is_zero, format_date
MAX_HASH_VERSION = 2


class AccountMove(models.Model):
    _inherit = "account.move"

    is_withholding = fields.Boolean("Is Withholding ?",
                                    compute='_compute_is_withholding')

    @api.depends('invoice_line_ids')
    def _compute_is_withholding(self):
        for rec in self:
            withholding_line = rec.invoice_line_ids.filtered(lambda line: line.name == 'Withholding Payment').mapped("name")
            if withholding_line and rec.move_type == 'entry':
                rec.is_withholding = True
            else:
                rec.is_withholding = False

    def _post(self, soft=True):
        """Post/Validate the documents.

        Posting the documents will give it a number, and check that the document is
        complete (some fields might not be required if not posted but are required
        otherwise).
        If the journal is locked with a hash table, it will be impossible to change
        some fields afterwards.

        :param soft (bool): if True, future documents are not immediately posted,
            but are set to be auto posted automatically at the set accounting date.
            Nothing will be performed on those documents before the accounting date.
        :return Model<account.move>: the documents that have been posted
        """
        for rec in self:
            if rec.move_type == 'entry':
                rec.state = 'draft'
        if soft:
            future_moves = self.filtered(
                lambda move: move.date > fields.Date.context_today(self))
            future_moves.auto_post = True
            for move in future_moves:
                msg = _(
                    'This move will be posted at the accounting date: %(date)s',
                    date=format_date(self.env, move.date))
                move.message_post(body=msg)
            to_post = self - future_moves
        else:
            to_post = self

        # `user_has_group` won't be bypassed by `sudo()` since it doesn't change the user anymore.
        if not self.env.su and not self.env.user.has_group(
                'account.group_account_invoice'):
            raise AccessError(
                _("You don't have the access rights to post an invoice."))
        for move in to_post:
            if move.move_type == 'in_invoice' and move.company_id.account_fiscal_country_id.code == 'IL':
                if not move.ref:
                    raise UserError(
                        _("The Bill/Refund Bill Reference is required to validate this document."))
        return super(AccountMove, self)._post(soft=soft)

    def action_register_payment(self):
        ''' Open the account.payment.register wizard to pay the selected journal entries.
        :return: An action opening the account.payment.register wizard.
        '''
        for rec in self:
            active_id = self.browse(self._context.get('active_id'))
            invoice_type = False
            if active_id and active_id.move_type == 'out_invoice' and active_id.company_id.withholding_tax_process and len(
                    self._context.get('active_ids')) == 1:
                invoice_type = True
            elif not active_id and rec.move_type == 'out_invoice' and rec.company_id.withholding_tax_process:
                invoice_type = True
            if invoice_type:
                withholding_tax_process = True
                return {
                    'name': _('Register Payment'),
                    'res_model': 'account.payment.register',
                    'view_mode': 'form',
                    'context': {
                        'active_model': 'account.move',
                        'active_ids': self.ids,
                        'default_withholding_tax_process': withholding_tax_process
                    },
                    'target': 'new',
                    'type': 'ir.actions.act_window',
                }
        return super(AccountMove, self).action_register_payment()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def _get_default_line_name(self, document, amount, currency, date,
                               partner=None):
        ''' Helper to construct a default label to set on journal items.

        E.g. Vendor Reimbursement $ 1,555.00 - Azure Interior - 05/14/2020.

        :param document:    A string representing the type of the document.
        :param amount:      The document's amount.
        :param currency:    The document's currency.
        :param date:        The document's date.
        :param partner:     The optional partner.
        :return:            A string.
        '''
        from odoo.tools.misc import formatLang, format_date
        values = ['%s %s' % (
            document, formatLang(self.env, amount, currency_obj=currency))]
        if partner:
            values.append(partner.display_name)
        values.append(
            format_date(self.env, fields.Date.to_string(date)))
        return ' - '.join(values)