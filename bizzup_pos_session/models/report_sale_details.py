# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, api


class ReportSaleDetails(models.AbstractModel):
    _inherit = "report.point_of_sale.report_saledetails"

    @api.model
    def get_sale_details(
            self, date_start=False, date_stop=False, config_ids=False,
            session_ids=False
    ):
        data = super().get_sale_details(date_start, date_stop, config_ids,
                                        session_ids)
        session_name = data.get(
            "session_name") if "session_name" in data else None
        sessions = self.env["pos.session"].search(
            [("name", "=", session_name)])

        data.update(
            {
                "company": sessions.company_id.name,
                "company_vat": sessions.company_id.vat,
            }
        )
        pos_cashier = self._context.get("pos_cashier", False)
        for session in sessions:
            session.env["pos.session.report.history"].sudo().create(
                {
                    "pos_id": session.id,
                    "user_id": session.env.user.id if not pos_cashier else pos_cashier,
                    "report_print_time": datetime.now(),
                }
            )
        return data
