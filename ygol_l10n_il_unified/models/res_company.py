# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

from odoo import fields, models


class ResCompany(models.Model):
    """Company class inherited to add report related data."""

    _inherit = "res.company"

    def _default_report_path(self):
        path = "/home/"
        return path

    software_registration_number = fields.Char(
        string="Application reg. no.",
        default="66666666",
        help="Registration no. of the application in the ITA system",
    )
    software_name = fields.Char(string="Software Name", default="Odoo")
    software_edition = fields.Char(string="software Edition", default="15.0CE")
    software_manufacture_number = fields.Char(
        string="Software Manufacture Number", default="1859"
    )
    software_type = fields.Selection(
        [("1", "Single year"), ("2", "Multi-year")],
        string="Application Type",
        default="2",
    )
    accounting_software_type = fields.Selection(
        [("1", "Cash basis,"), ("2", "Double Entry Accounting")],
        string="Accounting Type",
        default="2",
    )
    accounting_balance_requires = fields.Selection(
        [("1", "Entry level"), ("2", "Batch level")],
        string="Required accounting balancing",
        default="2",
    )
    information_on_branches = fields.Selection(
        [
            ("0", "the business has no branches."),
            ("1", "the business has branches/industries,"),
        ],
        default="0",
        string="Information on Branches",
    )
    start_date_wizard = fields.Date(string="Start Date")
    end_date_wizard = fields.Date(string="end Date")
    current_date = fields.Date(default=fields.Date.today())
    current_time = fields.Char()
    path_save_file_location = fields.Char(default=r"F:\OPENFRMT\ 00000009.07\ 07171025")
    # This fields we use for report 2.0 (type : Account Accounting)
    # Acceptance Information report :
