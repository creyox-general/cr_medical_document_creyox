# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

import re
from odoo import models, fields, api, _


class ResPartner(models.Model):
    """
    Inherits the res.partner model to add a non-mandatory TAZ field.
    The TAZ field accepts numeric input only and should be exactly 9 digits long.
    A soft warning is displayed if the input does not meet the criteria, but the record is still saved.
    """
    _inherit = 'res.partner'

    taz = fields.Char(
        string='TAZ',
        help='TAZ field - should be 9 digits long (numbers only)'
    )

    @api.onchange('taz')
    def _onchange_taz(self):
        """
        #HT01720
        Clean non-digit characters and warn user if invalid.
        """
        if self.taz:
            # Remove any non-digit characters
            clean_taz = re.sub(r'\D', '', self.taz)
            if clean_taz != self.taz:
                self.taz = clean_taz

            # Show warning if not exactly 9 digits
            if not re.match(r'^\d{9}$', self.taz):
                return {
                    'warning': {
                        'title': _('TAZ Format Warning'),
                        'message': _('TAZ must be exactly 9 digits (0–9). This record will still be saved.')
                    }
                }
