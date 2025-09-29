# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    allow_all_users_print_report = fields.Boolean(
        string="All users to print report")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env["ir.config_parameter"].sudo()
        allow_all_users_print_report = params.get_param(
            "allow_all_users_print_report", default=False
        )
        res.update(allow_all_users_print_report=allow_all_users_print_report)
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "allow_all_users_print_report", self.allow_all_users_print_report
        )

        group_allow_all_user = self.env.ref(
            "bizzup_pos_session.group_allow_all_user_from_pos_session"
        )
        group_pos_manager = self.env.ref(
            "point_of_sale.group_pos_manager"
        )  # Reference to the POS Manager group

        if self.allow_all_users_print_report:
            pos_manager_users = self.env["res.users"].search([])
            pos_manager_users.write(
                {"groups_id": [(4, group_allow_all_user.id)]})
        else:
            pos_users = self.env["res.users"].search(
                [("groups_id", "not in", group_pos_manager.id)]
            )
            for user in pos_users:
                user.groups_id = [(3, group_allow_all_user.id)]
