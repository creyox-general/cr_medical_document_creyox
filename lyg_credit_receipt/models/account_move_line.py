from collections import defaultdict
from contextlib import contextmanager
from datetime import date, timedelta
from functools import lru_cache

from odoo import api, fields, models, Command, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import (
    frozendict,
    formatLang,
    format_date,
    float_compare,
    Query,
)
from odoo.tools.sql import create_index
import logging

_logger = logging.getLogger(__name__)
tax_value = 0.0


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _check_amls_exigibility_for_reconciliation(
        self, shadowed_aml_values=None
    ):
        """Ensure the current journal items are eligible to be reconciled together.
        :param shadowed_aml_values: A mapping aml -> dictionary to replace some original aml values to something else.
                                    This is usefull if you want to preview the reconciliation before doing some changes
                                    on amls like changing a date or an account.
        """
        new_ctx = self._context.copy()
        new_ctx.update({"credit_receipt": False})
        if not self:
            return
        if any(aml.reconciled for aml in self):
            raise UserError(
                _(
                    "You are trying to reconcile some entries that are already reconciled."
                )
            )
        if (
            "credit_receipt" not in self._context
            or not self._context["credit_receipt"]
        ):
            if any(aml.parent_state != "posted" for aml in self):
                raise UserError(_("You can only reconcile posted entries."))
        accounts = self.mapped(
            lambda x: x._get_reconciliation_aml_field_value(
                "account_id", shadowed_aml_values
            )
        )
        if len(accounts) > 1:
            raise UserError(
                _(
                    "Entries are not from the same account: %s",
                    ", ".join(accounts.mapped("display_name")),
                )
            )
        if len(self.company_id.root_id) > 1:
            raise UserError(
                _(
                    "Entries don't belong to the same company: %s",
                    ", ".join(self.company_id.mapped("display_name")),
                )
            )
        if not accounts.reconcile and accounts.account_type not in (
            "asset_cash",
            "liability_credit_card",
        ):
            raise UserError(
                _(
                    "Account %s does not allow reconciliation. First change the configuration of this account "
                    "to allow it.",
                    accounts.display_name,
                )
            )
