# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.wizard'

    def action_create_payment(self):    
        """
        Creates a payment and marks related payments as refunds if applicable.
        """
        refund_payment = super().action_create_payment()
        receipt_ids = self.env['lyg.account.receipt'].browse(self._context.get('active_ids'))
        for receipt in receipt_ids:
            if hasattr(receipt, 'normal_receipt'):
                if receipt.normal_receipt and receipt.normal_receipt.payment_ids:
                    receipt.normal_receipt.payment_ids.is_refund = True
            else:
                if receipt and receipt.payment_ids:
                    receipt.payment_ids.is_refund = True
        return refund_payment
