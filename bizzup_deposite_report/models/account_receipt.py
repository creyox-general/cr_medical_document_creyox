# -*- coding: utf-8 -*-

from odoo import fields, models, api


class AccountReceipt(models.Model):
    _inherit = 'lyg.account.receipt'

    def action_post_receipt(self):
        """
        Overrides the receipt posting action to mark payments as refunds if specific conditions are met.
        """
        # Check if the field 'normal_receipt' exists in the model
        if 'normal_receipt' not in self._fields:
            return super(AccountReceipt, self).action_post_receipt()
        else:
            generic_pay = super(AccountReceipt, self).action_post_receipt()
            for receipt in self:
                if receipt.receipt_line_ids.filtered(lambda r: r.type == 'generic'):
                    if not receipt.normal_receipt:
                        return True
                    if receipt.normal_receipt and receipt.normal_receipt.payment_ids and receipt.payment_ids:
                        receipt.normal_receipt.payment_ids.is_refund = True
            return generic_pay
