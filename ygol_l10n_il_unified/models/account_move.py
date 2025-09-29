from datetime import date

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    # def _get_transaction_type(self):
    #     move_type = self._context.get("default_move_type", "")
    #     if move_type == "out_invoice":
    #         return [
    #             ("S", "Regular Sale"),
    #             ("L", "Private Customer"),
    #             ("Y", "Export"),
    #             ("I", "Palestinian Authority Customer"),
    #         ]
    #     elif move_type == "in_invoice":
    #         return [
    #             ("T", "Regular Supplier"),
    #             ("K", "Petty Cash"),
    #             ("R", "Import"),
    #             ("P", "Palestinian Authority Supplier"),
    #             ("C", "Input Self Invoice"),
    #         ]
    #     else:
    #         return []
    #
    # @api.model
    # def _default_type(self):
    #     move_type = self._context.get("default_move_type", "")
    #     if move_type == "out_invoice":
    #         return "S"
    #     elif move_type == "in_invoice":
    #         return "T"
    #     else:
    #         return ""
    #
    # transaction_type_document = fields.Selection(
    #     selection=_get_transaction_type, string="Document Type", default=_default_type
    # )

    transaction_type_document_out_invoice = fields.Selection([
        ("S", "Regular Sale"),
        ("L", "Private Customer"),
        ("M", "Self Invoice"),
        ("Y", "Export"),
        ("I", "Palestinian Authority Customer"),
    ], string="Document Type", default="S")

    transaction_type_document_in_invoice = fields.Selection([
        ("T", "Regular Supplier"),
        ("K", "Petty Cash"),
        ("R", "Import"),
        ("P", "Palestinian Authority Supplier"),
        ("H", "Single document by law "),
        ("C", "Input Self Invoice")
    ], string="Document Type", default="T")

    palestinian_invoice_number = fields.Char(string="Voucher Number")
    import_note_number = fields.Char(string="Import Note Number")
    posting_date = fields.Date("And/Or Posting date", copy=False)

    def action_post(self):
        """Function inherited to add posting date."""
        res = super(AccountMove, self).action_post()
        self.posting_date = date.today()
        return res

    def _reverse_moves(self, default_values_list=None, cancel=False):
        # OVERRIDE to pass value of transaction type as false
        if not default_values_list:
            default_values_list = [{} for move in self]
        for move, default_values in zip(self, default_values_list):
            default_values.update(
                {
                    "transaction_type_document_out_invoice": False,
                    "transaction_type_document_in_invoice": False,
                    "posting_date": False
                }
            )
        return super()._reverse_moves(
            default_values_list=default_values_list, cancel=cancel
        )
