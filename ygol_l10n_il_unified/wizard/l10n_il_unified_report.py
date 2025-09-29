# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

import base64
import io
import re
import logging
import random
import pytz
from contextlib import closing
from datetime import datetime, time
from itertools import groupby
from zipfile import ZipFile
from .bwEDI import convert_unified_format, convert_summary_document

from lxml import etree

from odoo import _, fields, models
from odoo.exceptions import UserError

# from langdetect import detect
_logger = logging.getLogger(__name__)


class FieldLinker:
    def __init__(self):
        self._last = 0
        self.map: dict[str, int] = {}

    def reset(self):
        self._last = 0
        self.map = {}

    def __getitem__(self, item):
        item = str(item)
        try:
            return self.map[item]
        except KeyError:
            self._last += 1
            self.map[item] = self._last
            return self._last


FIELD_LINKER = FieldLinker()

DOCUMENT_MODEL_MAPPING = {
    # Order
    100: (
        ["sale.order"],
        "date_order",
        [("state", "in", ["sale", "done", "paid", "invoiced"])],
    ),
    # shipping certificate(delivery) - C100
    200: (
        ["stock.picking"],
        "scheduled_date",
        [
            ("picking_type_id.code", "=", "outgoing"),
            ("sale_id", "!=", None),
            ("state", "in", ["done", "cancel"]),
        ],
    ),
    # Return certificate(delivery)
    210: (
        ["stock.picking"],
        "date_done",
        [
            ("picking_type_code", "=", "incoming"),
            ("sale_id", "!=", None),
            ("state", "in", ["done"]),
        ],
    ),
    # Invoice - C100 & B100
    305: (
        ["account.move"],
        "invoice_date",
        [
            ("move_type", "=", "out_invoice"),
            ("state", "in", ["posted", "cancel"]),
            ("journal_id.is_hmk", "=", False),
        ],
    ),
    # Credit Note - C100 & B100
    330: (
        ["account.move"],
        "invoice_date",
        [("move_type", "=", "out_refund"),
         ("state", "in", ["posted", "cancel"])],
    ),
    # Journal types Moves(payment) - C100, D120 & B100
    # HMK Invoices
    320: (
        ["account.move"],
        "date",
        [
            ("state", "=", "posted"),
            ("move_type", "=", "out_invoice"),
            ("is_hmk", "=", True),
        ],
    ),
    # Receipt M100
    400: (["lyg.account.receipt"],
          "date",
          [("state", "=", "post")]),
    405: (
        ["lyg.account.receipt"],
        "date",
        [("state", "=", "post"), ("is_donation", "=", True)],
    ),
    # Bank depositing
    420: (
        ["account.payment"],
        "date",
        [
            ("payment_type", "=", "inbound"),
            ("journal_id.type", "=", "bank"),
            ("state", "not in", ["draft", "cancelled"]),
        ],
    ),
    # Purchase Order
    500: (["purchase.order"],
          "date_order",
          [("state", "in", ["purchase", "done"])]),
    # Goods Receipt PO(Receipt)
    600: (
        ["stock.picking"],
        "date_done",
        [
            ("picking_type_code", "=", "incoming"),
            ("purchase_id", "!=", None),
            ("state", "not in", ["draft", "cancel"]),
        ],
    ),
    # Purchase Return(receipt)
    610: (
        ["stock.picking"],
        "date_done",
        [
            ("picking_type_code", "=", "outgoing"),
            ("purchase_id", "!=", None),
            ("state", "not in", ["draft", "cancel"]),
        ],
    ),
    # Purchase Tax Invoice(Vendor Bill) - B100
    700: (
        ["account.move"],
        "invoice_date",
        [("move_type", "=", "in_invoice"),
         ("state", "=", "posted")],
    ),
    # All Account move line - B100
    710: (["account.move"],
          "invoice_date",
          [("move_type", "=", "in_refund")]),
    # Account Move line with income account
    800: (["account.move.line"],
          "date",
          [("parent_state", "=", "posted")]),
    # Valuation of stock with qty and costing - M100
    810: (["stock.valuation.layer"],
          "date",
          []),
    # Outgoing Stock- D110
    820: (
        ["stock.move"],
        "date",
        [("picking_code", "=", "outgoing"),
         ("state", "not in", ["draft", "cancel"])],
    ),
    # Transfer between warehouses - M100
    830: (
        ["stock.move"],
        "date",
        [("picking_code", "=", "internal"),
         ("state", "not in", ["draft", "cancel"])],
    ),
    # Outgoing Stock - M100
    840: (
        ["stock.move"],
        "date",
        [("picking_code", "=", "outgoing"),
         ("state", "!=", ["draft", "cancel"])],
    ),
    # Production report - Login - M100
    900: (
        ["stock.move"],
        "date",
        [("raw_material_production_id", "!=", None),
         ("state", "=", "done")],
    ),
    # Production report - exit - M100
    910: (
        ["stock.move"],
        "date",
        [("production_id", "!=", None),
         ("state", "=", "done")],
    ),
}

d110_lines = {
    "sale.order": ["order_line"],
    "purchase.order": ["order_line"],
    "account.move": ["invoice_line_ids", "payment_lines"],
    "stock.move": ["move_lines"],
    "stock.picking": ["move_ids_without_package"],
}
# global variable to count record by its type
a000_counter = 0
c100_counter = 0
d110_counter = 0
d120_counter = 0
b100_counter = 0
b110_counter = 0
m100_counter = 0
z900_counter = 0
docs_counter = 0
primary_id = str(random.randint(1, 1000000000000000))


class UnifiedReport(models.TransientModel):
    """Class Added to Extract TXT report."""

    _name = "l10n_il.unified.report"
    _description = "Unified Report"

    # Fields
    date_from = fields.Date(
        "From", default=datetime.now().date().replace(month=1, day=1)
    )
    date_to = fields.Date("To", default=datetime.now().date().replace(month=12, day=31))
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    state = fields.Selection([("choose", "choose"), ("get", "get")], default="choose")
    extraction_summary_data = fields.Binary(
        "Extraction Summary Report", readonly=True, attachment=False
    )
    extraction_summary_filename = fields.Char()
    extraction_data = fields.Binary("Unified Report", readonly=True, attachment=False)
    extraction_filename = fields.Char()

    unified_report_2_6_data = fields.Binary(
        "Unified Report 2.6", readonly=True, attachment=False
    )
    unified_report_summary_filename = fields.Char()

    def search_codes(self, codes):
        """Function return only installed module codes."""
        code_list = []
        for code in codes:
            model_list = DOCUMENT_MODEL_MAPPING[code][0]
            code_model = self.env["ir.model"].search([("model", "in", model_list)])
            if code_model:
                code_list.append(code)
        return code_list

    def search_ini_txt(self):
        """Function call to pass INI.txt data. Total length : 466"""
        list_data = {'A000': {
            "entry_code": "A000",  # 1000
            "future_use_space_1": "00000",  # 1001
            "total_record_bkmvdata": docs_counter,  # 1002
            "authorized_dealer_number": self.env.company.vat,  # 1003
            "primary_id": primary_id,  # 1004
            "system_constant": "&OF1.31&",  # 1005
            "software_registration_number": self.env.company.software_registration_number,  # 1006
            "software_name": self.env.company.software_name,  # 1007
            "software_edition": self.env.company.software_edition,  # 1008
            "software_manufacture_number": self.env.company.software_manufacture_number,  # 1009
            "software_manufacturer_name": self.env.company.software_manufacture_number,  # 1010
            "software_type": self.env.company.software_type,  # 1011
            "file_path": self.env.company.path_save_file_location,  # 1012
            "accounting_software_type": self.env.company.accounting_software_type,  # 1013
            "accounting_balance_requires": self.env.company.accounting_balance_requires,  # 1014
            "registrar_number": self.env.company.vat,  # 1015
            "withholdings_file_number": None,  # 1016
            # "future_use_space_2": None,  # 1017
            "business_name": self.env.company.name,  # 1018
            "business_address_street": self.env.company.street,  # 1019
            "business_address_house_number": self.env.company.street2,  # 1020
            "business_address_city": self.env.company.city,  # 1021
            "business_address_zip_code": self.env.company.zip,  # 1022
            # Temp data passed as 'year' for tzx_year
            "tax_year": self.date_to.year,  # 1023
            "start_date": self.date_from.strftime("%Y%m%d"),  # 1024
            "end_date": datetime.today().strftime("%Y%m%d"),  # 1025
            "current_date_process": self.env.company.current_date.strftime("%Y%m%d"),  # 1026
            # Temp data pass as '0000' for current_time
            "current_time_process": datetime.now().strftime("%H%M"),  # 2027
            "language_code": "0",  # 2028
            "character_set": "2",  # 2029
            "zip_software_name": self.env.company.software_name,
            "leading_currency": "ILS",  # 1032
            "information_on_branches": self.env.company.information_on_branches,
        },
            'counters': {
                'C100': c100_counter,
                "D110": d110_counter,
                "D120": d120_counter,
                "B100": b100_counter,
                "B110": b110_counter,
                "M100": m100_counter,
            }}
        return list_data

    def a100_data(self):
        """Function call to pass A100 data."""
        a100_record = []
        a100_record_dic = {
            "entry_code": "A100",
            # Record number in the file updated below
            "authorized_dealer_number": self.env.company.vat,
            "primary_id": primary_id,
            "system_constant": "&OF1.31&"
        }
        a100_record.append(a100_record_dic)
        return a100_record

    def c100_data(self, codes=(100, 200, 305, 320, 330, 400, 405, 420, 500, 600, 610, 700, 710)):
        """Function call to get document data (Invoice&picking)C100."""
        c100_records = []
        codes = self.search_codes(codes)
        for code in codes:
            date_field = DOCUMENT_MODEL_MAPPING[code][1]
            model_list = DOCUMENT_MODEL_MAPPING[code][0]
            for model in model_list:
                search_domain = list(filter(lambda x: hasattr(self.env[model], x[0].split(".")[0]),
                                            DOCUMENT_MODEL_MAPPING[code][2]))
                search_domain += [(date_field, ">=", self.date_from), (date_field, "<=", self.date_to)]

                if "company_id" in self.env[model]._fields:
                    search_domain += [("company_id", "=", self.env.company.id)]
                rec_ids = self.env[model].search(search_domain)
                for record in rec_ids.filtered(lambda l: l.receipt_id if code == 420 else l):

                    purchase = record.purchase_id if hasattr(record, 'purchase_id') else ""
                    sales = record.sale_id if hasattr(record, 'sale_id') else ""
                    date_value = total_discount = amount_before_discount = ""
                    customer_supplier_id = record.partner_id.vat
                    amount_after_discount = 0
                    vat = 0
                    currency_amount = amount_withholding_tax = amount_includes_vat = 0.0
                    document_date = False
                    if code in [305, 320, 330, 700, 710, 100, 500]:
                        # Get date, discount and total discount, withholding amount
                        # for each below mentioned codes
                        amount_includes_vat = record.amount_total
                        if code not in [100, 500]:
                            record.invoice_date.strftime("%Y%m%d")
                            document_date = record.date.strftime("%Y%m%d")
                            total_discount = sum([line.price_subtotal for line in record.line_ids.filtered(
                                lambda a: a.product_id.discount_product)])

                            amount_before_discount = record.amount_untaxed
                            amount_withholding_tax = 0.0

                            customer_supplier_id = record.ref
                            amount_after_discount = record.amount_untaxed
                        if code in [100, 500]:
                            document_date = record.date_order.strftime("%Y%m%d")
                            amount_after_discount = record.amount_untaxed
                            # Get date, discount and total discount for each below-mentioned codes

                            total_discount = sum([line.price_subtotal for line in record.order_line.filtered(
                                lambda a: a.product_id.discount_product)])
                            amount_before_discount = record.amount_untaxed
                            customer_supplier_id = record.client_order_ref if code == 100 else record.partner_ref

                        if record.currency_id != self.env.company.currency_id:
                            currency_amount = record.amount_total_signed
                    elif code in [400, 405, 420]:
                        # Ger dare and withholding amount for receipt and
                        amount_includes_vat = (record.amount if code == 420 else record.total_pay_amount)
                        currency_amount = (record.move_id.amount_total_in_currency_signed if code == 420 else record.total_ils)
                        customer_supplier_id = record.partner_id.vat
                        amount_after_discount = record.move_id.total_pay_amount if record._name == 'account.payment' else record.total_pay_amount
                        document_date = record.create_date.strftime("%Y%m%d")
                    else:
                        purchase_amount_untaxed = record.purchase_id.amount_untaxed if hasattr(record,
                                                                                               'purchase_id') else ""
                        sales_amount_untaxed = record.sale_id.amount_untaxed if hasattr(record, 'sale_id') else ""
                        amount_after_discount = (
                                sales_amount_untaxed
                                or purchase_amount_untaxed
                        )
                        # record.scheduled_date.strftime("%Y%m%d")
                    # for record in rec_ids.filtered(
                    # lambda l:l.journal_id.is_hmk == True if code == 320 else l):
                    # dict to append data
                    currency_id = False
                    if record._name != "stock.picking":
                        currency_id = record.currency_id.name
                    elif sales:
                        document_date = record.sale_id.date_order.strftime("%Y%m%d")
                        currency_amount = record.sale_id.amount_total
                        currency_id = record.sale_id.currency_id.name
                        total_discount = sum([line.price_subtotal for line in record.sale_id.order_line.filtered(
                            lambda a: a.product_id.discount_product)])
                        amount_before_discount = record.sale_id.amount_untaxed
                        amount_includes_vat = record.sale_id.amount_total
                        vat = record.sale_id.amount_tax
                    elif purchase:
                        document_date = record.purchase_id.date_order.strftime("%Y%m%d")
                        currency_amount = record.purchase_id.amount_total
                        currency_id = record.purchase_id.currency_id.name
                        total_discount = sum([line.price_subtotal for line in record.purchase_id.order_line.filtered(
                            lambda a: a.product_id.discount_product)])
                        amount_before_discount = record.purchase_id.amount_untaxed
                        amount_includes_vat = record.purchase_id.amount_total
                        vat = record.purchase_id.amount_tax
                    else:
                        currency_id = record.company_id.currency_id.name
                        document_date = record.scheduled_date.strftime('%Y%m%d')
                    if code == 420:
                        document_date = record.date.strftime("%Y%m%d")
                    if code == 200:  # Fix for 1267 issue.
                        if record.sale_id:
                            total_discount = sum([line.price_subtotal for line in
                                                  record.sale_id.order_line.filtered(
                                                      lambda
                                                          a: a.product_id.discount_product)])
                            amount_before_discount = record.sale_id.amount_untaxed
                            document_date = record.sale_id.date_order.strftime(
                                "%Y%m%d") if (
                                    hasattr(record,
                                            'sale_id') and record.sale_id) \
                                else record.create_date.strftime('%Y%m%d')
                        else:
                            total_discount = sum(
                                [line.price_subtotal for line in
                                 record.purchase_id.order_line.filtered(
                                     lambda
                                         a: a.product_id.discount_product)])
                            amount_before_discount = record.purchase_id.amount_untaxed
                    product_id = None
                    if code in [100, 200, 305, 320, 330, 400, 420, 500, 600, 610, 700,  # TODO: 405?
                                710] and record._name != "lyg.account.payment.line":

                        if hasattr(record, "order_line"):
                            lines = record.order_line
                        elif hasattr(record, "move_ids_without_package"):
                            lines = record.move_ids_without_package
                        elif hasattr(record, "invoice_line_ids"):
                            lines = record.invoice_line_ids
                        elif hasattr(record, "receipt_line_ids"):
                            lines = record.receipt_line_ids
                        else:
                            lines = None

                        if lines:

                            if code != 400:
                                for d110_line in lines:
                                    if hasattr(d110_line, "display_type"):
                                        display_type = d110_line.display_type
                                    elif hasattr(d110_line, "display_type"):  # todo: same condition?
                                        display_type = d110_line.sale_line_id.display_type
                                    else:
                                        display_type = d110_line.purchase_line_id.display_type

                                    if not product_id and display_type not in ('line_note', 'line_section'):
                                        product_id = d110_line.product_id

                            if product_id is not None or code == 400:
                                c100_record_dic = {
                                    "entry_code": "C100",
                                    # Record number in the file updated below
                                    "authorized_dealer_number": self.env.company.vat,
                                    "document_type": code,
                                    "document_number": record.id,
                                    "document_production_date": document_date,
                                    "document_production_time": record.create_date.time().strftime("%H%M"),
                                    "consumer_supplier_name": record.partner_id.name,
                                    "consumer_supplier_street": record.partner_id.street,
                                    "consumer_supplier_house_number": record.partner_id.street2,
                                    "consumer_supplier_city": record.partner_id.city,
                                    "consumer_supplier_zip": record.partner_id.zip,
                                    "consumer_supplier_country": record.partner_id.country_id.name or "Israel",
                                    "consumer_supplier_country_code": record.partner_id.country_id.code or "IL",
                                    "consumer_supplier_phone": record.partner_id.phone,
                                    "authorized_supplier_customer_num": record.partner_id.vat,
                                    "date_value": date_value,
                                    "doc_sum_amount_foreign_currency": currency_amount,
                                    "foreign_currency_code": currency_id,
                                    # TODO: the sum of this field does not match with the sum of field 1267 in D110 in document 200 # have made changes for this
                                    "amount_before_discount": amount_before_discount,
                                    "discount_amount": total_discount,
                                    "amount_after_discount": amount_after_discount,
                                    "vat_amount": record.amount_tax if code in [305, 320, 330, 700, 710, 100,
                                                                                500] else vat,
                                    "amount_includes_vat": amount_includes_vat or 0.0,
                                    "amount_withholding_tax": amount_withholding_tax or 0.0,
                                    "customer_supplier_id": customer_supplier_id if customer_supplier_id else self.env.company.vat,
                                    # "match_field": "0",
                                    "deleted_document": "1" if record.state == "cancel" else "0",
                                    "document_date": document_date,
                                    "branch_id": None,
                                    "user": self.env.user.name,
                                    "field_linking_to_row": record.id,
                                    # "space_future_data": None,
                                }
                                # Append all values of C100

                                c100_records.append(c100_record_dic)

        c100_records = sorted(c100_records, key=lambda k: k["document_production_date"])
        return c100_records

    def d110_data(self, codes=(100, 200, 305, 320, 330, 500, 600, 610, 700, 710)):
        """Function call to get document data(move&stock lines) - D110."""
        d110_records = []
        codes = self.search_codes(codes)
        for code in codes:
            date_field = DOCUMENT_MODEL_MAPPING[code][1]
            model_list = DOCUMENT_MODEL_MAPPING[code][0]
            for model in model_list:
                search_domain = list(filter(lambda x: hasattr(self.env[model], x[0].split(".")[0]),
                                            DOCUMENT_MODEL_MAPPING[code][2], ))
                search_domain += [(date_field, ">=", self.date_from), (date_field, "<=", self.date_to)]

                if "company_id" in self.env[model]._fields:
                    search_domain += [("company_id", "=", self.env.company.id)]
                rec_ids = self.env[model].search(search_domain)
                if d110_lines.get(rec_ids._name):
                    iteration = 0
                    counter = 0
                    fields_len = len(d110_lines.get(rec_ids._name))
                    for field in d110_lines.get(rec_ids._name):
                        iteration += 1
                        if fields_len <= 1:
                            counter = 0
                        elif iteration > fields_len:
                            counter = 0
                        for record in getattr(rec_ids, field):
                            counter += 1
                            quantity = 0
                            amount_1267 = 0
                            base_document_type = ""
                            base_document_number = ""
                            manufacturer_name = ""
                            uom = ""
                            description_of_goods = ''
                            product_id = ''
                            total_discount = 0

                            unit_price_without_vat = 0
                            if code in [305, 320, 330, 700, 710]:
                                # Invoice, Bill, Credit note and HMK Invoice line's
                                # some of the fields value
                                if code != 320 and record._name != "lyg.account.payment.line":
                                    if code == 305:
                                        base_document_type = (100 if hasattr(record, "sale_line_ids") else "")
                                        base_document_number = (record.sale_line_ids.order_id.id
                                                                if hasattr(record, "sale_line_ids") else "")
                                        quantity = record.quantity
                                        total_discount = record.price_subtotal * record.discount

                                    elif code in [330, 710]:
                                        base_document_type = (300 if record.move_id.reversed_entry_id else "")
                                        base_document_number = (record.move_id.reversed_entry_id.id
                                                                if record.move_id.reversed_entry_id else "")
                                        quantity = record.quantity
                                        uom = record.product_uom_id.name

                                    elif code == 700:
                                        base_document_type = (500 if hasattr(record, "purchase_line_id") else "")
                                        base_document_number = (record.purchase_line_id.order_id.id
                                                                if hasattr(record, "purchase_line_id") else "")
                                        uom = record.product_uom_id.name
                                        quantity = record.quantity

                                    if record._name != "lyg.account.payment.line":
                                        if record.product_id and record.product_id.seller_ids:
                                            manufacturer_name = record.product_id.seller_ids[-1].partner_id.name

                                        vat_rate_line = record.tax_ids.compute_all(price_unit=record.price_subtotal
                                                                                   ).get("taxes")
                                        if vat_rate_line and "id" in vat_rate_line[0]:
                                            tax_amount = self.env['account.tax'].browse(vat_rate_line[0].get('id'))
                                            vat_rate_line = tax_amount.amount
                                        field_linking_to_title = record.move_id
                                        document_date = record.move_id.date.strftime("%Y%m%d")
                                        internal_number = record.product_id.default_code

                                else:
                                    if record._name == "lyg.account.payment.line":
                                        invoice_line_quantity = record.pay_invoice_id.invoice_line_ids.mapped(
                                            "quantity")
                                        quantity = sum(invoice_line_quantity)
                                        amount_1267 = record.pay_invoice_id.amount_untaxed
                                        percent_amount = (
                                                                     record.pay_invoice_id.amount_tax / record.pay_invoice_id.amount_total) * 100
                                        vat_rate_line = round(percent_amount)
                                        field_linking_to_title = record.pay_invoice_id
                                        document_date = record.pay_invoice_id.date.strftime("%Y%m%d")
                                        internal_number = ""
                                    else:
                                        uom = record.product_uom_id.name
                                        quantity = record.quantity
                                        if record.product_id.seller_ids:
                                            manufacturer_name = record.product_id.seller_ids[-1].partner_id.name

                                        vat_rate_line = record.tax_ids.compute_all(price_unit=record.price_subtotal
                                                                                   ).get("taxes")
                                        if vat_rate_line and "id" in vat_rate_line[0]:
                                            tax_amount = self.env['account.tax'].browse(vat_rate_line[0].get('id'))
                                            vat_rate_line = tax_amount.amount
                                        field_linking_to_title = record.move_id
                                        document_date = record.move_id.date.strftime("%Y%m%d")
                                        internal_number = record.product_id.default_code

                            elif code in [100, 500]:
                                # Sales & Purchase order line's some of the fields value
                                uom = record.product_uom.name
                                if record.product_id.seller_ids:
                                    manufacturer_name = record.product_id.seller_ids[-1].partner_id.name

                                if record.price_total:
                                    percent_amount = (record.price_tax / record.price_total) * 100
                                else:
                                    percent_amount = 0

                                vat_rate_line = round(percent_amount)
                                field_linking_to_title = record.order_id
                                document_date = record.order_id.date_order.strftime("%Y%m%d")
                                internal_number = record.product_id.default_code
                                amount_1267 = record.price_subtotal

                                if code == 100:
                                    quantity = record.product_uom_qty
                                    if not quantity:
                                        continue
                                    unit_price_without_vat = (record.price_subtotal / quantity) / (
                                            1 - (record.discount / 100))
                                    total_discount = (unit_price_without_vat * record.product_uom_qty * record.discount
                                                      / 100)

                                elif code == 500:
                                    quantity = record.product_qty
                                    document_date = record.order_id.date_order.strftime("%Y%m%d")
                                    total_discount = 0

                            elif code == 200:
                                total_discount = ((record.sale_line_id.price_unit *
                                                   record.sale_line_id.product_uom_qty) *
                                                  record.sale_line_id.discount / 100 if
                                                  hasattr(record, 'sale_line_id') else 0)
                                amount_vat = ((record.sale_line_id.price_total - record.sale_line_id.price_subtotal)
                                              / record.sale_line_id.product_uom_qty if
                                              record.sale_line_id.product_uom_qty else 1) if (
                                    hasattr(record, 'sale_line_id')) else ""

                                unit_price_without_vat = record.sale_line_id.price_unit - amount_vat if (
                                    hasattr(record, 'sale_line_id')) else ""
                                amount_1267 = record.sale_line_id.product_uom_qty * unit_price_without_vat if (
                                    hasattr(record, 'sale_line_id')) else ""
                                percent_amount = 0
                                if record.sale_line_id.price_total:
                                    percent_amount = (
                                                                 record.sale_line_id.price_tax / record.sale_line_id.price_total) * 100 if (
                                        hasattr(record, 'sale_line_id')) else ""
                                vat_rate_line = round(percent_amount)
                                if hasattr(record, 'sale_line_id'):
                                    uom = record.sale_line_id.product_uom.name
                                if hasattr(record, 'sale_line_id'):
                                    quantity = record.sale_line_id.product_uom_qty
                                if record.product_id.seller_ids:
                                    manufacturer_name = record.product_id.seller_ids[-1].partner_id.name

                                field_linking_to_title = record.picking_id
                                document_date = record.sale_line_id.order_id.date_order.strftime("%Y%m%d") if (
                                        hasattr(record, 'sale_line_id') and record.sale_line_id) \
                                    else record.create_date.strftime('%Y%m%d')

                                internal_number = record.product_id.default_code

                            elif code == 600:
                                total_discount = 0
                                amount_1267 = record.purchase_line_id.price_subtotal if hasattr(record,
                                                                                                'purchase_line_id') else ""
                                unit_price_without_vat = record.purchase_line_id.price_unit if (
                                    hasattr(record, 'purchase_line_id')) else ""
                                uom = record.purchase_line_id.product_uom.name if (
                                    hasattr(record, 'purchase_line_id')) else ""
                                quantity = record.purchase_line_id.product_qty if (
                                    hasattr(record, 'purchase_line_id')) else 0
                                if record.product_id.seller_ids:
                                    manufacturer_name = record.product_id.seller_ids[-1].partner_id.name

                                percent_amount = 0
                                if record.sale_line_id.price_total:
                                    percent_amount = (record.purchase_line_id.price_tax /
                                                      record.purchase_line_id.price_total) * 100 if (
                                                      hasattr(record, 'purchase_line_id')) else ""

                                vat_rate_line = round(percent_amount)
                                field_linking_to_title = record.picking_id
                                document_date = record.purchase_line_id.order_id.date_approve.strftime("%Y%m%d") if (
                                    hasattr(record, 'purchase_line_id')) else record.create_date.strftime('%Y%m%d')
                                internal_number = record.product_id.default_code
                                unit_price_without_vat = record.purchase_line_id.price_unit if (
                                    hasattr(record, 'purchase_line_id')) else ""

                            else:
                                # Stock line's some of the fields value
                                uom = record.product_uom.name
                                quantity = record.product_uom_qty
                                if record.product_id.seller_ids:
                                    manufacturer_name = record.product_id.seller_ids[-1].partner_id.name

                                vat_rate_line = 0
                                field_linking_to_title = record.picking_id
                                document_date = record.picking_id.scheduled_date.strftime("%Y%m%d")

                                base_document_type = 100 if hasattr(record, 'sale_id') else 500 if (
                                    hasattr(record, 'purchase_id')) else ""

                                base_document_number = record.sale_id.id if hasattr(record, 'sale_id') else (
                                    record.purchase_id.id) if hasattr(record, 'purchase_id') else ""
                                internal_number = record.product_id.default_code

                            transaction_type = 3
                            if ((code in [100, 200, 305, 330, 500, 600, 610, 700, 710] and
                                    record._name != "lyg.account.payment.line") or
                                    (code == 320 and record._name == "account.move.line")):
                                if record.product_id.type == "service":
                                    transaction_type = 1
                                elif record.product_id.type == "product":
                                    transaction_type = 2

                            if code in [100, 305, 320, 330, 500, 610, 700, 710]:

                                if quantity and record._name in ["account.move.line", 'sale.order.line']:
                                    unit_price_without_vat = (record.price_subtotal / quantity) / (
                                            1 - (record.discount / 100))
                                    total_discount = unit_price_without_vat * quantity * record.discount / 100
                                    # logging.warning(f"ZERO: {record.price_subtotal} | {record.quantity} | {record.discount}")
                                elif not unit_price_without_vat and hasattr(record, "price_unit"):
                                        unit_price_without_vat = record.price_unit

                            if code in [320, 330, 610, 700, 710]:

                                if hasattr(record, "discount") and hasattr(record, "price_unit") and not total_discount:
                                    total_discount = record.price_unit * quantity * record.discount / 100

                                if record._name in ["lyg.account.move.line", "lyg.account.payment.line",
                                                    "account.move.line"]:
                                    amount_1267 = record.price_subtotal if hasattr(record, "price_subtotal") else (
                                        record.amount) if hasattr(record, "amount") else ""


                            if record._name == "account.move.line":
                                amount_1267 = record.price_subtotal

                            if code == 330 and record._name == "account.move.line":
                                quantity = record.quantity

                            if code == 610 and record._name == 'stock.move':
                                if hasattr(record, "sale_line_id"):
                                    amount_1267 = record.sale_line_id.price_subtotal if record.sale_line_id else ""
                                    unit_price_without_vat = record.sale_line_id.price_unit if record.sale_line_id else ""
                                if hasattr(record, "purchase_line_id"):
                                    amount_1267 = record.purchase_line_id.price_subtotal if record.purchase_line_id else ""
                                    unit_price_without_vat = record.purchase_line_id.price_unit if record.purchase_line_id else ""
                                    vat_rate_line = record.purchase_line_id.taxes_id.compute_all(
                                        price_unit=record.purchase_line_id.price_subtotal
                                        ).get("taxes")
                                    if vat_rate_line and "id" in \
                                            vat_rate_line[0]:
                                        tax_amount = self.env[
                                            'account.tax'].browse(
                                            vat_rate_line[0].get('id'))
                                        vat_rate_line = tax_amount.amount

                            if code == 100 and record._name == 'sale.order.line':
                                if amount_1267:
                                    vat_rate_line = record.tax_id.compute_all(price_unit=record.price_subtotal
                                                                              ).get("taxes")
                                    if vat_rate_line and "id" in vat_rate_line[0]:
                                        tax_amount = self.env['account.tax'].browse(vat_rate_line[0].get('id'))
                                        vat_rate_line = tax_amount.amount

                            if code == 320 and record._name == 'account.move.line':
                                tax_calculation = record.price_total - record.price_subtotal
                                percent_amount = 0
                                if record.price_total:
                                    percent_amount = (tax_calculation / record.price_total) * 100
                                vat_rate_line = round(percent_amount)

                            if code == 320 and record._name == 'lyg.account.payment.line':
                                unit_price_without_vat = record.pay_invoice_id.amount_untaxed
                                amount_1267 = record.pay_invoice_id.amount_untaxed

                            if code == 305:
                                if hasattr(record, "price_subtotal"):
                                    amount_1267 = record.price_subtotal
                                elif hasattr(record, "amount"):
                                    amount_1267 = record.amount
                                else:
                                    amount_1267 = ""

                            if (code in [100, 200, 305, 330, 500, 600, 610, 700, 710] and
                                    record._name != "lyg.account.payment.line") or (
                                    code == 320 and record._name == "account.move.line"):
                                description_of_goods = record.product_id.name
                                product_id = record.product_id

                            if product_id and quantity:
                                if record._name != 'lyg.account.payment.line':
                                    d110_record_dic = {
                                        "entry_code": "D110",
                                        # Record number in the file updated below
                                        "authorized_dealer_number": self.env.company.vat,
                                        "document_type": code,
                                        # field_linking_to_title means header document id and here name of header record
                                        # So, used above variable with name and below with ID
                                        "document_number": field_linking_to_title.id,
                                        "row_number_in_the_document": counter,
                                        "base_document_type": base_document_type,
                                        "base_document_number": base_document_number,
                                        "transaction_type": transaction_type,
                                        "internal_number": internal_number,
                                        "description_of_goods": description_of_goods,
                                        "manufacturer_name": manufacturer_name,
                                        "product_serial_number": internal_number,
                                        "uom": uom,
                                        "quantity": quantity,
                                        "unit_price_without_vat": unit_price_without_vat,
                                        "discount_line": -total_discount,
                                        "total_amount_line": amount_1267,
                                        "vat_rate_line": vat_rate_line if not isinstance(vat_rate_line, list) else 0,
                                        # TODO: sometimes is [] # Added condition for [] and replaced with zero.
                                        "branch_id": None,
                                        "document_date": document_date,
                                        # field_linking_to_title it is parent linked title (id)
                                        "field_linking_to_title": field_linking_to_title.id,
                                        "branch_id_for_base_document": None,
                                        # "future_data_space": None,
                                    }

                                    d110_records.append(d110_record_dic)

        return d110_records

    def d120_data(self, codes=(400, 405, 420)):
        """Function call to get document data(payment) - d120."""
        d120_records = []
        codes = self.search_codes(codes)
        for code in codes:
            date_field = DOCUMENT_MODEL_MAPPING[code][1]
            model_list = DOCUMENT_MODEL_MAPPING[code][0]
            for model in model_list:
                search_domain = list(filter(lambda x: hasattr(self.env[model], x[0].split(".")[0]),
                                            DOCUMENT_MODEL_MAPPING[code][2]))
                # search domain
                search_domain += [(date_field, ">=", self.date_from), (date_field, "<=", self.date_to)]

                if "company_id" in self.env[model]._fields:
                    search_domain += [("company_id", "=", self.env.company.id)]
                rec_ids = self.env[model].search(search_domain)
                counter = 0
                # added filter to search cash and bank move lines
                for record in rec_ids.filtered(lambda l: l._name == "account.payment" and l.receipt_id):
                    name = re.sub(r'[^0-9]', '', record.name)
                    if code == 420:
                        name = record.name.split('/')[-1]

                    counter += 1
                    d120_record_dic = {
                        "entry_code": "D120",
                        # Record number in the file updated below
                        "authorized_dealer_number": self.env.company.vat,
                        "document_type": code,
                        "document_number": record.id,
                        "row_number": counter,
                        "payment_method_type": record.means_of_payment,
                        "bank_number": record.bank_number,
                        "branch_number": record.branch_number,
                        "account_number": record.account_number,
                        "check_number": record.lyg_check_number,
                        "check_payment_due_date": record.check_payment_due_date.strftime("%Y%m%d") if
                        record.journal_id.type == "bank" and record.check_payment_due_date else None,
                        "row_amount": record.amount,
                        "company_code_clears": record.comp_code_clears,
                        "clearing_card_name": record.credit_card_name,
                        "credit_transaction_type": record.credit_transaction_type,
                        "branch_id": None,
                        "document_date": record.date.strftime("%Y%m%d") if record else None,
                        "field_linking_to_the_title": record.id,
                        # "future_data_space": None,
                    }
                    # append dict of D120
                    d120_records.append(d120_record_dic)

                for record in rec_ids.filtered(lambda l: l._name == "lyg.account.receipt"):
                    for line in record.receipt_line_ids:
                        name = "400" + line.pay_receipt_id.name[9:] if len(line.pay_receipt_id.name) == 14 else re.sub(
                            r'[^0-9]', '', line.pay_receipt_id.name)
                        counter += 1
                        d120_record_dic = {
                            "entry_code": "D120",
                            # Record number in the file updated below
                            "authorized_dealer_number": self.env.company.vat,
                            "document_type": code,
                            "document_number": line.pay_receipt_id.id,
                            "row_number": counter,
                            "payment_method_type": line.means_of_payment,
                            "bank_number": line.bank_id.bank_code,
                            "branch_number": line.branch,
                            "account_number": line.credit_account_no,
                            "check_number": line.voucher_check_no,
                            "check_payment_due_date": line.validity_date.strftime("%Y%m%d") if
                            line.journal_id.type == "bank" and line.validity_date else None,
                            "row_amount": line.amount,
                            "company_code_clears": None,
                            "clearing_card_name": None,
                            "credit_transaction_type": None,
                            "branch_id": None,
                            "document_date": record.create_date.strftime("%Y%m%d") if record else None,
                            "field_linking_to_the_title": line.pay_receipt_id.id,
                            # "future_data_space": None,
                        }
                        # append dict of D120
                        d120_records.append(d120_record_dic)

        return d120_records

    def b100_data(self, codes=(305, 320, 330, 700, 710)):
        """Function return account move line data - B100."""
        b100_record = []
        codes = self.search_codes(codes)
        move_counter = 0
        for code in codes:
            date_field = DOCUMENT_MODEL_MAPPING[code][1]
            model_list = DOCUMENT_MODEL_MAPPING[code][0]
            for model in model_list:
                search_domain = DOCUMENT_MODEL_MAPPING[code][2]
                search_domain += [(date_field, ">=", self.date_from), (date_field, "<=", self.date_to)]
                if "company_id" in self.env[model]._fields:
                    search_domain += [("company_id", "=", self.env.company.id)]
                rec_ids = self.env[model].search(search_domain)

                def key_func(k):
                    """Function for group by field."""
                    return k["account_id"] or (183, '200000 Product Sales')

                product = self.env["product.product"]
                for record in rec_ids:
                    currency_amount = 0.0
                    if record.currency_id != self.env.company.currency_id:
                        currency_amount = record.amount_total_signed
                    move_counter += 1
                    # read line's data of all account.move
                    list_data = record.line_ids.read()
                    # sorted list by key(account_id)
                    info = sorted(list_data, key=key_func)
                    final_income = total_discount_amount = income_amount = 0.0
                    # group by all lines and data with account_id
                    action_mark = 1
                    for key, value in groupby(info, key_func):
                        value = list(value)
                        # Get list of discount line using product flag
                        total_discount_filter = list(map(lambda l: l["price_subtotal"], filter(
                            lambda x: x["product_id"] and product.browse(x["product_id"][0]).discount_product, value)))
                        # sum of all the discount lines of move
                        total_discount_amount += sum(total_discount_filter)
                        # Get list of income lines(product sales)
                        income_filter = list(map(lambda l: l["price_subtotal"], filter(
                            lambda x: x["account_internal_group"] and x["account_internal_group"] == "income", value)))
                        # sum of all the income account's amount
                        income_amount += sum(income_filter)
                        final_income = income_amount + total_discount_amount
                    # to access above variable value need one more loop
                    counter_move_line = 0
                    for key, value in groupby(info, key_func):
                        value = list(value)
                        # amount_of_action = 0.0
                        counter_account = ""
                        if list(filter(lambda l: not product.browse(l["product_id"] and
                                                                    l["product_id"][0]).discount_product, value)):
                            counter_move_line += 1
                            if list(filter(lambda x: x["account_internal_group"] and
                                                     x["account_internal_group"] == "income", value)):
                                amount_of_action = final_income
                            else:
                                amount_of_action = value[0].get("balance")
                            quantity = str(int(value[0].get("quantity")))
                            dabit = value[0].get("dabit")
                            credit = value[0].get("credit")
                            account_group = value[0].get("account_internal_group")
                            if account_group == "expence" and dabit:
                                action_mark = 1
                            elif account_group == "income" and credit:
                                action_mark = 2
                            for transaction in record.transaction_ids:
                                if transaction.payment_id:
                                    # As per the document I have tried to add the account of the records whose payment has been done by Cash Basis.
                                    # I am not sure if this is proper, but I've given it a try, but we need to consult with someone regarding this
                                    counter_account = transaction.payment_id.journal_id.default_account_id.code if transaction.payment_id.means_of_payment == '1' else None
                            b100_record_dic = {
                                # 1350
                                "entry_code": "B100",
                                # Record number in the file updated below - # 1351
                                # 1352
                                "authorized_dealer_number": self.env.company.vat,
                                # 1353
                                "transactions_number": move_counter,
                                # 1354
                                "transactions_row_number": counter_move_line,
                                # Temp pass move_id and dose is as Batch(1355)
                                "batch": record.id,
                                # 1356
                                "transactions_type": record.journal_id.type,
                                # 1357
                                "reference": record.name,
                                # 1358
                                "reference_document_type": code,
                                # 1359
                                "reference2": None,
                                # 1360
                                "reference_document_type2": None,
                                # 1361
                                # 'details': self.count_length('DEMO CON', 50),
                                "details": value[0].get("name").replace("\n", "") or None,
                                # 1362
                                "date": record.posting_date.strftime(
                                    "%Y%m%d") if record.posting_date else record.date.strftime("%Y%m%d"),
                                # 1363
                                "value_date": record.date.strftime("%Y%m%d"),
                                # 1364
                                "transacting_account": value[0].get("account_id", ["", ""])[1].split(" ")[0] or None,
                                # 1365
                                "counter_account": counter_account,
                                # 1366 TODO: need to update = not sure what need to pass # Added a counter account please check the comment above the variable 'counter_account'
                                "transaction_code": action_mark,
                                # 1367
                                "foreign_currency_code": record.currency_id.name,
                                # 1368
                                "transaction_amount": amount_of_action,
                                # 1369
                                "foreign_currency_amount": currency_amount,
                                # 1370
                                "quantity_field": quantity,
                                # 1371
                                "adjustment_field1": None,
                                # 1372
                                "adjustment_field2": value[0].get("matching_number"),
                                # as of now need to pass null value. 1374
                                "branch_id": None,
                                # 1375
                                "order_date": record.create_date.strftime("%Y%m%d"),
                                # 1376
                                "user": record.user_id.name,
                                # 1377
                                # "future_data_space": None,
                            }
                            b100_record.append(b100_record_dic)
                            # List sorted with Trans number(move sequence)
                            b100_record = sorted(
                                b100_record, key=lambda k: k["transactions_number"]
                            )
        return b100_record

    def b110_data(self, codes=(800,)):
        """Function return account data - B110."""
        b110_records = []
        codes = self.search_codes(codes)
        for code in codes:
            # date_field = DOCUMENT_MODEL_MAPPING[code][1]
            model_list = DOCUMENT_MODEL_MAPPING[code][0]
            for model in model_list:
                search_domain = list(filter(lambda x: hasattr(self.env[model], x[0].split(".")[0]),
                                            DOCUMENT_MODEL_MAPPING[code][2]))
                if "company_id" in self.env[model]._fields:
                    search_domain += [("company_id", "=", self.env.company.id)]

                rec_ids = self.env[model].search(search_domain)
                opening_bal_data = rec_ids.filtered(lambda l: l.date < self.date_from)
                between_dates_data = rec_ids.filtered(lambda l: self.date_from <= l.date <= self.date_to)
                for account in rec_ids.mapped("account_id"):
                    opening_bal_move_lines = opening_bal_data.filtered(lambda a: a.account_id.id == account.id)
                    opening_bal_currency_amount = sum(opening_bal_move_lines.mapped("amount_currency"))
                    # opening_bal_currency = (opening_bal_move_lines.mapped("currency_id").name or "ILS")
                    opening_balance = (sum(opening_bal_move_lines.mapped("credit")) -
                                       sum(opening_bal_move_lines.mapped("debit")))
                    between_move_lines = between_dates_data.filtered(lambda a: a.account_id.id == account.id)
                    credit_amount = sum(between_move_lines.mapped("credit"))
                    debit_amount = sum(between_move_lines.mapped("debit"))

                    b110_record_dic = {
                        # 1400
                        "entry_code": "B110",
                        # Record number in the file updated below # 1401
                        # 1402
                        "authorized_dealer_number": self.env.company.vat,
                        # 1403 code
                        "account_code": account.code,
                        # 1404 name
                        "account_name": account.name or "PLACEHOLDER",
                        # 1405
                        "test_balance_code": (account.group_id.code_prefix_start +
                                              account.group_id.code_prefix_end) or None,
                        # 1406
                        "description_of_test_balance_code": account.group_id.name,
                        # 1407
                        "client_supplier_street": None,
                        # 1408
                        "customer_supplier_street2": None,
                        # 1409
                        "customer_supplier_address_city": None,
                        # 1410
                        "customer_supplier_address_zip": None,
                        # 1411
                        "customer_supplier_address_country": None,
                        # 1412
                        "country_code": account.company_ids.country_id.code or "IL",
                        # 1413 Summary account
                        "Summary_account": None,
                        # 1414
                        "beginning_balance": opening_balance,
                        # 1415 Total debit
                        "total_debit": debit_amount,
                        # 1416 Total credit
                        "total_credit": credit_amount,
                        # 1417
                        "accounting_classification_code": None,
                        # 1419
                        "supplier_customer_dealer_no": None,
                        # 1421
                        "branch_id": None,
                        # 1422
                        "beginning_bal_foreign_currency": opening_bal_currency_amount,
                        # 1423
                        "curr_code_acc_balance_at_opp_cutoff": rec_ids.mapped("currency_id").name or "ILS",
                        # 1421
                        # "future_data_space": None,
                    }
                    b110_records.append(b110_record_dic)
        return b110_records

    def m100_data(self, codes=(810,)):
        """Function return stock move data - M100."""
        m100_record = []
        codes = self.search_codes(codes)
        for code in codes:
            # date_field = DOCUMENT_MODEL_MAPPING[code][1]
            model_list = DOCUMENT_MODEL_MAPPING[code][0]
            for model in model_list:
                search_domain = list(filter(lambda x: hasattr(self.env[model], x[0].split(".")[0]),
                                            DOCUMENT_MODEL_MAPPING[code][2]))

                if "company_id" in self.env[model]._fields:
                    search_domain += [("company_id", "=", self.env.company.id)]
                rec_ids = self.env[model].search(search_domain)

                start_time = time(0, 0)
                date_from = datetime.combine(self.date_from, start_time)
                time(23, 59)
                date_to = datetime.combine(self.date_to, start_time)
                opening_bal_layer = rec_ids.filtered(lambda l: l.create_date < date_from)
                between_dates_layer = rec_ids.filtered(
                    lambda l: l.create_date >= date_from and l.create_date <= date_to)
                available_products = rec_ids.mapped("product_id")
                for record in available_products:
                    if record.default_code:  # Condition to check if product has default code
                        # total_entrances = total_expenditure = 0
                        opening_bal_of_product = abs(sum(opening_bal_layer.filtered(
                            lambda l: l.product_id.id == record.id).mapped("quantity")))
                        # total_entrances = total_expenditure = 0
                        total_entrances = sum(between_dates_layer.filtered(
                            lambda l: l.product_id.id == record.id and l.quantity > 0).mapped("quantity"))
                        total_expenditure = sum(between_dates_layer.filtered(
                            lambda l: l.product_id.id == record.id and l.quantity < 0).mapped("quantity"))
                        cut_off_balance = sum(between_dates_layer.filtered(
                            lambda l: l.product_id.id == record.id).mapped("value"))
                        m100_record_dic = {
                            "entry_code": "M100",
                            # Record number in the file updated below
                            "authorized_dealer_number": self.env.company.vat,
                            "universal_catalog_number": record.barcode,
                            "supplier_manufacturer_catalog_number": record.description_purchase,
                            "internal_catalog_number": record.default_code,
                            "item_name": record.name,
                            "class_code": record.default_code,
                            "class_code_description": record.name,
                            "uom": record.uom_id.name,
                            "item_balance_at_the_beginning": opening_bal_of_product,
                            # 1461 : Total inventory increase
                            "total_inventory_increase": total_entrances,
                            # 1462 : Total inventory decrease
                            "total_inventory_decrease": total_expenditure,
                            # 1463 : Cut off balance (costing) at ending
                            "cost_price_inventory_out_cut_off": abs(cut_off_balance),
                            # as of now we will skip.
                            "cost_price_inventory_in_cut_off": None,
                            # "future_space": None,
                        }
                        m100_record.append(m100_record_dic)
                not_available_products = self.env["product.product"].search([("id", "not in", available_products.ids)])
                for record in not_available_products:
                    if record.default_code:
                        # total_entrances = total_expenditure = 0
                        opening_bal_of_product = abs(sum(opening_bal_layer.filtered(
                            lambda l: l.product_id.id == record.id).mapped("quantity")))
                        # total_entrances = total_expenditure = 0
                        total_entrances = sum(between_dates_layer.filtered(
                            lambda l: l.product_id.id == record.id and l.quantity > 0).mapped("quantity"))
                        total_expenditure = sum(between_dates_layer.filtered(
                            lambda l: l.product_id.id == record.id and l.quantity < 0).mapped("quantity"))
                        cut_off_balance = sum(between_dates_layer.filtered(
                            lambda l: l.product_id.id == record.id).mapped("value"))
                        m100_record_dic = {
                            "entry_code": "M100",
                            # Record number in the file updated below
                            "authorized_dealer_number": self.env.company.vat,
                            "universal_catalog_number": record.barcode,
                            "supplier_manufacturer_catalog_number": record.description_purchase,
                            "internal_catalog_number": record.default_code,
                            "item_name": record.name,
                            "class_code": record.default_code,
                            "class_code_description": record.name,
                            "uom": record.uom_id.name,
                            "item_balance_at_the_beginning": opening_bal_of_product,
                            # 1461 : Total inventory increase
                            "total_inventory_increase": total_entrances,
                            # 1462 : Total inventory increase
                            "total_inventory_decrease": total_expenditure,
                            # 1463 : Cut off balance (costing) at ending
                            "cost_price_inventory_out_cut_off": abs(cut_off_balance),
                            # as of now we will skip.
                            "cost_price_inventory_in_cut_off": None,
                            "future_space": None,
                        }
                        m100_record.append(m100_record_dic)
        return m100_record

    def z900_data(self):
        """Function call to pass Z100 data."""
        z900_record = []
        z900_record_dic = {
            "entry_code": "Z900",
            # Record number in the file updated below
            "authorized_dealer_number": self.env.company.vat,
            "primary_id": primary_id,
            "system_constant": "&OF1.31&",
            # 'total_counter': Passed in function search_documents,
            # "future_space": None,
        }
        z900_record.append(z900_record_dic)
        return z900_record

    def search_documents(self):
        """Override the method for sending sales orders, purchase orders, and stock inventory data
        through BKMVDATA.TXT file. Simply append new document codes to 'codes' keyword argument before
        the super call.

        Method returns list of tuples. A tuple be like:
        (document code, browsable record,)

        For instance,
        (300, account.move(1,),)
        """
        global docs_counter, a000_counter, c100_counter, d110_counter, d120_counter, b100_counter, b110_counter, \
            m100_counter, z900_counter

        FIELD_LINKER.reset()

        docs_counter = 0
        all_records = {
            'A000': [],
            'A100': [],
            'C100': [],
            'D110': [],
            'D120': [],
            'B100': [],
            'B110': [],
            'M100': [],
            'Z900': [],
        }

        a100_rec_ids = self.a100_data()
        c100_rec_ids = self.c100_data(codes=[100, 200, 305, 320, 330, 400, 405, 420, 500, 600, 610, 700, 710])
        d110_rec_ids = self.d110_data(codes=[100, 200, 305, 320, 330, 500, 600, 610, 700, 710])
        d120_rec_ids = self.d120_data(codes=[400, 405, 420])
        b100_rec_ids = self.b100_data(codes=[305, 320, 330, 700, 710])
        b110_rec_ids = self.b110_data(codes=[800])
        m100_rec_ids = self.m100_data(codes=[810])
        z900_rec_ids = self.z900_data()

        # Append A100 record into list
        a100_counter = 0
        for record in a100_rec_ids:
            docs_counter += 1
            a100_counter += 1
            record.update({"counter": docs_counter})
            all_records["A100"].append(record)
        # Append C100 record into list
        c100_counter = 0
        for record in c100_rec_ids:
            c100_counter += 1
            docs_counter += 1
            record.update({"counter": docs_counter})
            all_records["C100"].append(record)
        # Append D110 record into list
        d110_counter = 0
        for record in d110_rec_ids:
            d110_counter += 1
            docs_counter += 1
            record.update({"counter": docs_counter})
            all_records["D110"].append(record)
        # append D120 record into list
        d120_counter = 0
        for record in d120_rec_ids:
            d120_counter += 1
            docs_counter += 1
            record.update({"counter": docs_counter})
            all_records["D120"].append(record)
        # Append B100 record into list
        b100_counter = 0
        for record in b100_rec_ids:
            b100_counter += 1
            docs_counter += 1
            record.update({"counter": docs_counter})
            all_records["B100"].append(record)
        # Append B110 record into list
        b110_counter = 0
        for record in b110_rec_ids:
            b110_counter += 1
            docs_counter += 1
            record.update({"counter": docs_counter})
            all_records["B110"].append(record)
        # Append M100 record into list
        m100_counter = 0
        for record in m100_rec_ids:
            m100_counter += 1
            docs_counter += 1
            record.update({"counter": docs_counter})
            all_records["M100"].append(record)
        # Append z900 record into list
        z900_counter = 0
        for record in z900_rec_ids:
            docs_counter += 1
            z900_counter += 1
            record.update({"counter": docs_counter, "total_counter": docs_counter})
            all_records["Z900"].append(record)

        _logger.info("\n\n ----------all_records----------b100_counter :\n%s", b100_counter)
        _logger.info("\n\n ----------all_records----------b110_counter :\n%s", b110_counter)
        _logger.info("\n\n ----------all_records----------c100_counter :\n%s", c100_counter)
        _logger.info("\n\n ----------all_records----------d110_counter :\n%s", d110_counter)
        _logger.info("\n\n ----------all_records----------d120_counter :\n%s", d120_counter)
        _logger.info("\n\n ----------all_records----------m100_counter :\n%s", m100_counter)
        _logger.info("\n\n ----------all_records----------z900_counter :\n%s", z900_counter)
        return all_records

    def document_type_counter(self):
        doc_codes = [100, 200, 205, 210, 300, 305, 310, 320, 330, 340, 345,
                     400, 405, 410, 420, 500, 600, 610, 700, 710, 800, 810,
                     820, 830, 840, 900, 910]
        doc_code_counts = {code: 0 for code in doc_codes}
        sums = {code: 0 for code in doc_codes}
        for k, records in self.search_documents().items():
            for record in records:
                doc_code = record.get("document_type")
                transaction_code = record.get("transaction_type")
                if record.get("entry_code") == 'C100':
                    if doc_code in doc_code_counts:
                        doc_code_counts[doc_code] += 1
                        if record.get("amount_includes_vat"):
                            amount = record.get("amount_includes_vat")
                            amount_includes_vat = int(amount)
                            sums[doc_code] += amount_includes_vat
                    elif transaction_code in doc_code_counts:
                        doc_code_counts[transaction_code] += 1
        return doc_code_counts, sums

    def generate(self):
        """Function call to generate report."""
        if self.env.company.account_fiscal_country_id.code != "IL":
            raise UserError(_("You can not print this report."))

        dir_company = self.env.company.l10n_il_withh_tax_id_number
        # warning  raised when there is no WHTID set at company.
        if not dir_company:
            raise UserError(_("Please add WHT ID in the company."))

        folder_list = []
        with closing(io.BytesIO()) as f:
            with ZipFile(f, "w") as archive:
                doc_data = convert_unified_format(
                    self.search_documents()).encode("iso8859_8", errors="replace")
                doc_data = doc_data.decode("iso8859_8").replace("?", " ").encode("iso8859_8")
                archive.writestr(f'{"/".join(folder_list)}/BKMVDATA.TXT', doc_data)

                summary_data = convert_summary_document(
                    self.search_ini_txt()).encode("iso8859_8", errors="replace")
                summary_data = summary_data.decode("iso8859_8").replace("?", " ").encode("iso8859_8")
                archive.writestr(f'{"/".join(folder_list)}/INI.TXT', summary_data)

            zip_data = f.getvalue()
        attachment_obj = self.env["ir.attachment"].create(
            {
                "name": "OPENFRMT.zip",
                "datas": base64.b64encode(zip_data),
            }
        )
        content, content_type = self.prepare_data_extraction_summary_report(
            abs_path=attachment_obj._full_path(attachment_obj.store_fname), summary=[]
        )
        unified_content, unified_content_type = self.prepare_unified_report_2_6(
            abs_path=attachment_obj._full_path(attachment_obj.store_fname),
            summary=[]
        )
        self.write({
            "state": "get",
            "extraction_summary_data": base64.encodebytes(content),
            "extraction_summary_filename": "Data_Extraction_Summary_Report_%s.pdf"
                                           % (datetime.now().date().strftime("%Y-%m-%d")),
            "extraction_data": attachment_obj.datas,
            "extraction_filename": attachment_obj.name,
            "unified_report_2_6_data": base64.encodebytes(
                unified_content),
            "unified_report_summary_filename": "Unified_Report_2_6_%s.pdf"
                                               % (datetime.now().date().strftime("%Y-%m-%d")),
        })

        return {
            'type': "ir.actions.act_window",
            "res_model": "l10n_il.unified.report",
            "view_mode": "form",
            "res_id": self.id,
            "views": [(False, "form")],
            "target": "new"
        }

    def get_user_current_time(self):
        user = self.env.user
        user_tz = pytz.timezone(user.tz)  # Get user's timezone
        current_time = datetime.now(tz=pytz.utc).astimezone(user_tz)
        return current_time  # Format the time as desired

    def prepare_data_extraction_summary_report(self, abs_path=None, summary=[]):
        """
        Data extraction summary report consists of:
            1. VAT ID number of the company
            2. Name of the company
            3. File saving path
            4. Dates range
            5. Summary of the data reported in BKMVDATA
            6. Name of the software (Odoo) and software registration number (
            TBD)
        """
        total_records = [a000_counter, c100_counter, d110_counter,
                         d120_counter, b100_counter, b110_counter,
                         m100_counter, z900_counter]
        current_time = self.get_user_current_time()
        total = sum(total_records)
        data = {
            "date_start": self.date_from,
            "date_end": self.date_to,
            "a100_counter": a000_counter,
            "c100_counter": c100_counter,
            "d110_counter": d110_counter,
            "d120_counter": d120_counter,
            "b100_counter": b100_counter,
            "b110_counter": b110_counter,
            "m100_counter": m100_counter,
            "z900_counter": z900_counter,
            "total_of_records": total,
            "current_tz": current_time
        }
        return self.env.ref(
            "ygol_l10n_il_unified.action_data_extraction_summary_report"
        )._render_qweb_pdf(report_ref="ygol_l10n_il_unified.action_data_extraction_summary_report", data=data)

    def prepare_unified_report_2_6(self, abs_path=None, summary=[]):
        document_codes = self.document_type_counter()
        total_codes_count = []
        total_of_amount = []
        current_time = self.get_user_current_time()
        for rec in document_codes[0].values():
            if int(rec) > 0:
                total_codes_count.append(int(rec))
        for amount in document_codes[1].values():
            if int(amount) > 0:
                total_of_amount.append(int(amount))
        data = {
            "date_start": self.date_from,
            "date_end": self.date_to,
            "total_codes_count": sum(total_codes_count),
            "total_of_amount": sum(total_of_amount),
            "current_tz": current_time,
            "100_counter": [document_codes[0].get(100),
                            document_codes[1].get(100)],
            "200_counter": [document_codes[0].get(200),
                            document_codes[1].get(200)],
            "205_counter": [document_codes[0].get(205),
                            document_codes[1].get(205)],
            "210_counter": [document_codes[0].get(210),
                            document_codes[1].get(210)],
            "300_counter": [document_codes[0].get(300),
                            document_codes[1].get(300)],
            "305_counter": [document_codes[0].get(305),
                            document_codes[1].get(305)],
            "310_counter": [document_codes[0].get(310),
                            document_codes[1].get(310)],
            "320_counter": [document_codes[0].get(320),
                            document_codes[1].get(320)],
            "330_counter": [document_codes[0].get(330),
                            document_codes[1].get(330)],
            "340_counter": [document_codes[0].get(340),
                            document_codes[1].get(340)],
            "345_counter": [document_codes[0].get(345),
                            document_codes[1].get(345)],
            "400_counter": [document_codes[0].get(400),
                            document_codes[1].get(400)],
            "405_counter": [document_codes[0].get(405),
                            document_codes[1].get(405)],
            "410_counter": [document_codes[0].get(410),
                            document_codes[1].get(410)],
            "420_counter": [document_codes[0].get(420),
                            document_codes[1].get(420)],
            "500_counter": [document_codes[0].get(500),
                            document_codes[1].get(500)],
            "600_counter": [document_codes[0].get(600),
                            document_codes[1].get(600)],
            "610_counter": [document_codes[0].get(610),
                            document_codes[1].get(610)],
            "700_counter": [document_codes[0].get(700),
                            document_codes[1].get(700)],
            "710_counter": [document_codes[0].get(710),
                            document_codes[1].get(710)],
            "800_counter": [document_codes[0].get(800),
                            document_codes[1].get(800)],
            "810_counter": [document_codes[0].get(810),
                            document_codes[1].get(810)],
            "820_counter": [document_codes[0].get(820),
                            document_codes[1].get(820)],
            "830_counter": [document_codes[0].get(830),
                            document_codes[1].get(830)],
            "840_counter": [document_codes[0].get(840),
                            document_codes[1].get(840)],
            "900_counter": [document_codes[0].get(900),
                            document_codes[1].get(900)],
            "910_counter": [document_codes[0].get(910),
                            document_codes[1].get(910)],
        }
        return self.env.ref("ygol_l10n_il_unified.action_unified_report_2_6_report")._render_qweb_pdf(
            report_ref="ygol_l10n_il_unified.action_unified_report_2_6_report", data=data)

    def export(self):
        """Export pass."""
        pass
