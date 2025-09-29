#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################
from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    # Added HMK type boolean
    is_hmk = fields.Boolean('HMK ?')


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    hmk_withholding_payment = fields.Boolean()
    is_hmk_payment = fields.Boolean()