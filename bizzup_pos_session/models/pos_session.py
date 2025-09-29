# -*- coding: utf-8 -*-
from odoo import models, fields


class PosSession(models.Model):
    _inherit = "pos.session"

    report_history_ids = fields.One2many(
        "pos.session.report.history",
        "pos_id",
    )

    def action_print_pos_session(self, pos_cashier):
        active_user = self.env["hr.employee"].sudo().browse(
            pos_cashier).user_id.id
        return (
            self.env.ref("point_of_sale.sale_details_report")
            .with_context(pos_cashier=active_user)
            .report_action(self)
        )

    def get_user_pos_session_group(self, pos_cashier):
        active_user = self.env["hr.employee"].sudo().browse(
            pos_cashier).user_id
        if active_user:
            group_allow_all_user_from_pos_session = active_user.has_group(
                "bizzup_pos_session.group_allow_all_user_from_pos_session"
            )
            if group_allow_all_user_from_pos_session:
                return True
        return False

