# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential


from odoo import api, models


class UnifiedReport26(models.AbstractModel):
    _name = "report.ygol_l10n_il_unified.unified_report_2_6"
    _description = "Unified Report 2.6"

    @api.model
    def _get_report_values(self, docids, data=None):
        return {"data": data}
