from .segment import Segment
from .element import Element


class A000(Segment):
    def __init__(self):
        Segment.__init__(self)

        self.id = Element(
            name="A000",
            content="A000",
        )
        self.fields.append(self.id)

        self.A000_01 = Element(
            name="A000_01",
            numeric=False,
            length=5
        )
        self.fields.append(self.A000_01)

        self.A000_02 = Element(
            name="A000_02",
            json_name="total_record_bkmvdata",
            numeric=True,
            length=15
        )
        self.fields.append(self.A000_02)

        self.A000_03 = Element(
            name="A000_03",
            json_name="authorized_dealer_number",
            numeric=True,
            length=9
        )
        self.fields.append(self.A000_03)

        self.A000_04 = Element(
            name="A000_04",
            json_name="primary_id",
            numeric=True,
            length=15
        )
        self.fields.append(self.A000_04)

        self.A000_05 = Element(
            name="A000_05",
            json_name="system_constant",
            numeric=False,
            length=8
        )
        self.fields.append(self.A000_05)

        self.A000_06 = Element(
            name="A000_06",
            json_name="software_registration_number",
            numeric=True,
            length=8
        )
        self.fields.append(self.A000_06)

        self.A000_07 = Element(
            name="A000_07",
            json_name="software_name",
            numeric=False,
            length=20
        )
        self.fields.append(self.A000_07)

        self.A000_08 = Element(
            name="A000_08",
            json_name="software_edition",
            numeric=False,
            length=20
        )
        self.fields.append(self.A000_08)

        self.A000_09 = Element(
            name="A000_09",
            json_name="software_manufacture_number",
            numeric=True,
            length=9
        )
        self.fields.append(self.A000_09)

        self.A000_10 = Element(
            name="A000_10",
            json_name="software_manufacturer_name",
            numeric=False,
            length=20
        )
        self.fields.append(self.A000_10)

        self.A000_11 = Element(
            name="A000_11",
            json_name="software_type",
            numeric=True,
            length=1
        )
        self.fields.append(self.A000_11)

        self.A000_12 = Element(
            name="A000_12",
            json_name="file_path",
            numeric=False,
            length=50
        )
        self.fields.append(self.A000_12)

        self.A000_13 = Element(
            name="A000_13",
            json_name="accounting_software_type",
            numeric=True,
            length=1
        )
        self.fields.append(self.A000_13)

        self.A000_14 = Element(
            name="A000_14",
            json_name="accounting_balance_requires",
            numeric=True,
            length=1
        )
        self.fields.append(self.A000_14)

        self.A000_15 = Element(
            name="A000_15",
            json_name="registrar_number",
            numeric=True,
            length=9
        )
        self.fields.append(self.A000_15)

        self.A000_16 = Element(
            name="A000_16",
            json_name="withholdings_file_number",
            numeric=True,
            length=9
        )
        self.fields.append(self.A000_16)

        self.A000_17 = Element(
            name="A000_17",
            numeric=False,
            length=10
        )
        self.fields.append(self.A000_17)

        self.A000_18 = Element(
            name="A000_18",
            json_name="business_name",
            numeric=False,
            length=50
        )
        self.fields.append(self.A000_18)

        self.A000_19 = Element(
            name="A000_19",
            json_name="business_address_street",
            numeric=False,
            length=50
        )
        self.fields.append(self.A000_19)

        self.A000_20 = Element(
            name="A000_20",
            json_name="business_address_house_number",
            numeric=False,
            length=10
        )
        self.fields.append(self.A000_20)

        self.A000_21 = Element(
            name="A000_21",
            json_name="business_address_city",
            numeric=False,
            length=30
        )
        self.fields.append(self.A000_21)

        self.A000_22 = Element(
            name="A000_22",
            json_name="business_address_zip_code",
            numeric=False,
            length=8
        )
        self.fields.append(self.A000_22)

        self.A000_23 = Element(
            name="A000_23",
            json_name="tax_year",
            numeric=True,
            length=4
        )
        self.fields.append(self.A000_23)

        self.A000_24 = Element(
            name="A000_24",
            json_name="start_date",
            numeric=True,
            length=8
        )
        self.fields.append(self.A000_24)

        self.A000_25 = Element(
            name="A000_25",
            json_name="end_date",
            numeric=True,
            length=8
        )
        self.fields.append(self.A000_25)

        self.A000_26 = Element(
            name="A000_26",
            json_name="current_date_process",
            numeric=True,
            length=8
        )
        self.fields.append(self.A000_26)

        self.A000_27 = Element(
            name="A000_27",
            json_name="current_time_process",
            numeric=True,
            length=4
        )
        self.fields.append(self.A000_27)

        self.A000_28 = Element(
            name="A000_28",
            json_name="language_code",
            numeric=True,
            length=1
        )
        self.fields.append(self.A000_28)

        self.A000_29 = Element(
            name="A000_29",
            json_name="character_set",
            numeric=True,
            length=1
        )
        self.fields.append(self.A000_29)

        self.A000_30 = Element(
            name="A000_30",
            json_name="zip_software_name",
            numeric=False,
            length=20
        )
        self.fields.append(self.A000_30)

        self.A000_32 = Element(
            name="A000_32",
            json_name="leading_currency",
            numeric=False,
            length=3
        )
        self.fields.append(self.A000_32)

        self.A000_34 = Element(
            name="A000_34",
            json_name="information_on_branches",
            numeric=True,
            length=1
        )
        self.fields.append(self.A000_34)

        self.A000_35 = Element(
            name="A000_35",
            numeric=False,
            length=46
        )
        self.fields.append(self.A000_35)

        self.field_count = len(self.fields) - 1


class A100(Segment):
    def __init__(self):
        Segment.__init__(self)

        self.id = Element(
            name="A100",
            content="A100",
        )
        self.fields.append(self.id)

        self.A100_01 = Element(
            name="A100_01",
            json_name="counter",
            numeric=True,
            length=9
        )
        self.fields.append(self.A100_01)

        self.A100_02 = Element(
            name="A100_02",
            json_name="authorized_dealer_number",
            numeric=True,
            length=9
        )
        self.fields.append(self.A100_02)

        self.A100_03 = Element(
            name="A100_03",
            json_name="primary_id",
            numeric=True,
            length=15
        )
        self.fields.append(self.A100_03)

        self.A100_04 = Element(
            name="A100_04",
            json_name="system_constant",
            numeric=False,
            length=8
        )
        self.fields.append(self.A100_04)

        self.A100_05 = Element(
            name="A100_05",
            numeric=False,
            length=50
        )
        self.fields.append(self.A100_05)

        self.field_count = len(self.fields) - 1


class Z900(Segment):
    def __init__(self):
        Segment.__init__(self)

        self.id = Element(
            name="Z900",
            content="Z900",
        )
        self.fields.append(self.id)

        self.Z900_01 = Element(
            name="Z900_01",
            json_name="counter",
            numeric=True,
            length=9
        )
        self.fields.append(self.Z900_01)

        self.Z900_02 = Element(
            name="Z900_02",
            json_name="authorized_dealer_number",
            numeric=True,
            length=9
        )
        self.fields.append(self.Z900_02)

        self.Z900_03 = Element(
            name="Z900_03",
            json_name="primary_id",
            numeric=True,
            length=15
        )
        self.fields.append(self.Z900_03)

        self.Z900_04 = Element(
            name="Z900_04",
            json_name="system_constant",
            numeric=False,
            length=8
        )
        self.fields.append(self.Z900_04)

        self.Z900_05 = Element(
            name="Z900_05",
            json_name="total_counter",
            numeric=True,
            length=15
        )
        self.fields.append(self.Z900_05)

        self.Z900_06 = Element(
            name="Z900_06",
            numeric=False,
            length=50
        )
        self.fields.append(self.Z900_06)

        self.field_count = len(self.fields) - 1


class C100(Segment):
    def __init__(self):
        Segment.__init__(self)

        self.id = Element(
            name="C100",
            content="C100",
        )
        self.fields.append(self.id)

        self.C100_01 = Element(
            name="C100_01",
            json_name="counter",
            numeric=True,
            length=9
        )
        self.fields.append(self.C100_01)

        self.C100_02 = Element(
            name="C100_02",
            json_name="authorized_dealer_number",
            numeric=True,
            length=9
        )
        self.fields.append(self.C100_02)

        self.C100_03 = Element(
            name="C100_03",
            json_name="document_type",
            numeric=True,
            length=3
        )
        self.fields.append(self.C100_03)

        self.C100_04 = Element(
            name="C100_04",
            json_name="document_number",
            numeric=False,
            length=20
        )
        self.fields.append(self.C100_04)

        self.C100_05 = Element(
            name="C100_05",
            json_name="document_production_date",
            numeric=True,
            length=8
        )
        self.fields.append(self.C100_05)

        self.C100_06 = Element(
            name="C100_06",
            json_name="document_production_time",
            numeric=True,
            length=4
        )
        self.fields.append(self.C100_06)

        self.C100_07 = Element(
            name="C100_07",
            json_name="consumer_supplier_name",
            numeric=False,
            length=50
        )
        self.fields.append(self.C100_07)

        self.C100_08 = Element(
            name="C100_08",
            json_name="consumer_supplier_street",
            numeric=False,
            length=50
        )
        self.fields.append(self.C100_08)

        self.C100_09 = Element(
            name="C100_09",
            json_name="consumer_supplier_house_number",
            numeric=False,
            length=10
        )
        self.fields.append(self.C100_09)

        self.C100_10 = Element(
            name="C100_10",
            json_name="consumer_supplier_city",
            numeric=False,
            length=30
        )
        self.fields.append(self.C100_10)

        self.C100_11 = Element(
            name="C100_11",
            json_name="consumer_supplier_zip",
            numeric=False,
            length=8
        )
        self.fields.append(self.C100_11)

        self.C100_12 = Element(
            name="C100_12",
            json_name="consumer_supplier_country",
            numeric=False,
            length=30
        )
        self.fields.append(self.C100_12)

        self.C100_13 = Element(
            name="C100_13",
            json_name="consumer_supplier_country_code",
            numeric=False,
            length=2
        )
        self.fields.append(self.C100_13)

        self.C100_14 = Element(
            name="C100_14",
            json_name="consumer_supplier_phone",
            numeric=False,
            length=15
        )
        self.fields.append(self.C100_14)

        self.C100_15 = Element(
            name="C100_15",
            json_name="authorized_supplier_customer_num",
            numeric=True,
            length=9
        )
        self.fields.append(self.C100_15)

        self.C100_16 = Element(
            name="C100_16",
            json_name="date_value",
            numeric=True,
            length=8
        )
        self.fields.append(self.C100_16)

        self.C100_17 = Element(
            name="C100_17",
            json_name="doc_sum_amount_foreign_currency",
            numeric=False,
            decimal=2,
            length=15
        )
        self.fields.append(self.C100_17)

        self.C100_18 = Element(
            name="C100_18",
            json_name="foreign_currency_code",
            numeric=False,
            length=3
        )
        self.fields.append(self.C100_18)

        self.C100_19 = Element(
            name="C100_19",
            json_name="amount_before_discount",
            numeric=False,
            decimal=2,
            length=15
        )
        self.fields.append(self.C100_19)

        self.C100_20 = Element(
            name="C100_20",
            json_name="discount_amount",
            numeric=False,
            decimal=2,
            length=15
        )
        self.fields.append(self.C100_20)

        self.C100_21 = Element(
            name="C100_21",
            json_name="amount_after_discount",
            numeric=False,
            decimal=2,
            length=15
        )
        self.fields.append(self.C100_21)

        self.C100_22 = Element(
            name="C100_22",
            json_name="vat_amount",
            numeric=False,
            decimal=2,
            length=15
        )
        self.fields.append(self.C100_22)

        self.C100_23 = Element(
            name="C100_23",
            json_name="amount_includes_vat",
            numeric=False,
            decimal=2,
            length=15
        )
        self.fields.append(self.C100_23)

        self.C100_24 = Element(
            name="C100_24",
            json_name="amount_withholding_tax",
            numeric=False,
            decimal=2,
            length=12
        )
        self.fields.append(self.C100_24)

        self.C100_25 = Element(
            name="C100_25",
            json_name="customer_supplier_id",
            numeric=False,
            length=15
        )
        self.fields.append(self.C100_25)

        self.C100_26 = Element(
            name="C100_26",
            numeric=False,
            length=10
        )
        self.fields.append(self.C100_26)

        self.C100_28 = Element(
            name="C100_28",
            json_name="deleted_document",
            numeric=True,
            length=1
        )
        self.fields.append(self.C100_28)

        self.C100_30 = Element(
            name="C100_30",
            json_name="document_date",
            numeric=True,
            length=8
        )
        self.fields.append(self.C100_30)

        self.C100_31 = Element(
            name="C100_31",
            json_name="branch_id",
            numeric=False,
            length=7
        )
        self.fields.append(self.C100_31)

        self.C100_33 = Element(
            name="C100_33",
            json_name="user",
            numeric=False,
            length=9
        )
        self.fields.append(self.C100_33)

        self.C100_34 = Element(
            name="C100_34",
            json_name="field_linking_to_row",
            numeric=True,
            length=7
        )
        self.fields.append(self.C100_34)

        self.C100_35 = Element(
            name="C100_35",
            numeric=False,
            length=13
        )
        self.fields.append(self.C100_35)

        self.field_count = len(self.fields) - 1


class D110(Segment):
    def __init__(self):
        Segment.__init__(self)

        self.id = Element(
            name="D110",
            content="D110",
        )
        self.fields.append(self.id)

        self.D110_01 = Element(
            name="D110_01",
            json_name="counter",
            numeric=True,
            length=9
        )
        self.fields.append(self.D110_01)

        self.D110_02 = Element(
            name="D110_02",
            json_name="authorized_dealer_number",
            numeric=True,
            length=9
        )
        self.fields.append(self.D110_02)

        self.D110_03 = Element(
            name="D110_03",
            json_name="document_type",
            numeric=True,
            length=3
        )
        self.fields.append(self.D110_03)

        self.D110_04 = Element(
            name="D110_04",
            json_name="document_number",
            numeric=False,
            length=20
        )
        self.fields.append(self.D110_04)

        self.D110_05 = Element(
            name="D110_05",
            json_name="row_number_in_the_document",
            numeric=True,
            length=4
        )
        self.fields.append(self.D110_05)

        self.D110_06 = Element(
            name="D110_06",
            json_name="base_document_type",
            numeric=True,
            length=3
        )
        self.fields.append(self.D110_06)

        self.D110_07 = Element(
            name="D110_07",
            json_name="base_document_number",
            numeric=False,
            length=20
        )
        self.fields.append(self.D110_07)

        self.D110_08 = Element(
            name="D110_08",
            json_name="transaction_type",
            numeric=True,
            length=1
        )
        self.fields.append(self.D110_08)

        self.D110_09 = Element(
            name="D110_09",
            json_name="internal_number",
            numeric=False,
            length=20
        )
        self.fields.append(self.D110_09)

        self.D110_10 = Element(
            name="D110_10",
            json_name="description_of_goods",
            numeric=False,
            length=30
        )
        self.fields.append(self.D110_10)

        self.D110_11 = Element(
            name="D110_11",
            json_name="manufacturer_name",
            numeric=False,
            length=50
        )
        self.fields.append(self.D110_11)

        self.D110_12 = Element(
            name="D110_12",
            json_name="product_serial_number",
            numeric=False,
            length=30
        )
        self.fields.append(self.D110_12)

        self.D110_13 = Element(
            name="D110_13",
            json_name="uom",
            numeric=False,
            length=20
        )
        self.fields.append(self.D110_13)

        self.D110_14 = Element(
            name="D110_14",
            json_name="quantity",
            numeric=False,
            decimal=4,
            length=17
        )
        self.fields.append(self.D110_14)

        self.D110_15 = Element(
            name="D110_15",
            json_name="unit_price_without_vat",
            numeric=False,
            decimal=2,
            length=15
        )
        self.fields.append(self.D110_15)

        self.D110_16 = Element(
            name="D110_16",
            json_name="discount_line",
            numeric=False,
            decimal=2,
            length=15
        )
        self.fields.append(self.D110_16)

        self.D110_17 = Element(
            name="D110_17",
            json_name="total_amount_line",
            numeric=False,
            decimal=2,
            length=15
        )
        self.fields.append(self.D110_17)

        self.D110_18 = Element(
            name="D110_18",
            json_name="vat_rate_line",
            numeric=True,
            decimal=2,
            length=4
        )
        self.fields.append(self.D110_18)

        self.D110_20 = Element(
            name="D110_20",
            json_name="branch_id",
            numeric=False,
            length=7
        )
        self.fields.append(self.D110_20)

        self.D110_22 = Element(
            name="D110_22",
            json_name="document_date",
            numeric=True,
            length=8
        )
        self.fields.append(self.D110_22)

        self.D110_23 = Element(
            name="D110_23",
            json_name="field_linking_to_title",
            numeric=True,
            length=7
        )
        self.fields.append(self.D110_23)

        self.D110_24 = Element(
            name="D110_24",
            json_name="branch_id_for_base_document",
            numeric=False,
            length=7
        )
        self.fields.append(self.D110_24)

        self.D110_25 = Element(
            name="D110_25",
            numeric=False,
            length=21
        )
        self.fields.append(self.D110_25)

        self.field_count = len(self.fields) - 1


class D120(Segment):
    def __init__(self):
        Segment.__init__(self)

        self.id = Element(
            name="D120",
            content="D120",
        )
        self.fields.append(self.id)

        self.D120_01 = Element(
            name="D120_01",
            json_name="counter",
            numeric=True,
            length=9
        )
        self.fields.append(self.D120_01)

        self.D120_02 = Element(
            name="D120_02",
            json_name="authorized_dealer_number",
            numeric=True,
            length=9
        )
        self.fields.append(self.D120_02)

        self.D120_03 = Element(
            name="D120_03",
            json_name="document_type",
            numeric=True,
            length=3
        )
        self.fields.append(self.D120_03)

        self.D120_04 = Element(
            name="D120_04",
            json_name="document_number",
            numeric=False,
            length=20
        )
        self.fields.append(self.D120_04)

        self.D120_05 = Element(
            name="D120_05",
            json_name="row_number",
            numeric=True,
            length=4
        )
        self.fields.append(self.D120_05)

        self.D120_06 = Element(
            name="D120_06",
            json_name="payment_method_type",
            numeric=False,
            length=1
        )
        self.fields.append(self.D120_06)

        self.D120_07 = Element(
            name="D120_07",
            json_name="bank_number",
            numeric=True,
            length=10
        )
        self.fields.append(self.D120_07)

        self.D120_08 = Element(
            name="D120_08",
            json_name="branch_number",
            numeric=True,
            length=10
        )
        self.fields.append(self.D120_08)

        self.D120_09 = Element(
            name="D120_09",
            json_name="account_number",
            numeric=True,
            length=15
        )
        self.fields.append(self.D120_09)

        self.D120_10 = Element(
            name="D120_10",
            json_name="check_number",
            numeric=True,
            length=10
        )
        self.fields.append(self.D120_10)

        self.D120_11 = Element(
            name="D120_11",
            json_name="check_payment_due_date",
            numeric=True,
            length=8
        )
        self.fields.append(self.D120_11)

        self.D120_12 = Element(
            name="D120_12",
            json_name="row_amount",
            numeric=False,
            decimal=2,
            length=15
        )
        self.fields.append(self.D120_12)

        self.D120_13 = Element(
            name="D120_13",
            json_name="company_code_clears",
            numeric=True,
            length=1
        )
        self.fields.append(self.D120_13)

        self.D120_14 = Element(
            name="D120_14",
            json_name="clearing_card_name",
            numeric=False,
            length=20
        )
        self.fields.append(self.D120_14)

        self.D120_15 = Element(
            name="D120_15",
            json_name="credit_transaction_type",
            numeric=True,
            length=1
        )
        self.fields.append(self.D120_15)

        self.D120_20 = Element(
            name="D120_20",
            json_name="branch_id",
            numeric=False,
            length=7
        )
        self.fields.append(self.D120_20)

        self.D120_22 = Element(
            name="D120_22",
            json_name="document_date",
            numeric=True,
            length=8
        )
        self.fields.append(self.D120_22)

        self.D120_23 = Element(
            name="D120_23",
            json_name="field_linking_to_the_title",
            numeric=True,
            length=7
        )
        self.fields.append(self.D120_23)

        self.D120_24 = Element(
            name="D120_24",
            numeric=False,
            length=60
        )
        self.fields.append(self.D120_24)

        self.field_count = len(self.fields) - 1


class B100(Segment):
    def __init__(self):
        Segment.__init__(self)

        self.id = Element(
            name="B100",
            content="B100",
        )
        self.fields.append(self.id)

        self.B100_01 = Element(
            name="B100_01",
            json_name="counter",
            numeric=True,
            length=9
        )
        self.fields.append(self.B100_01)

        self.B100_02 = Element(
            name="B100_02",
            json_name="authorized_dealer_number",
            numeric=True,
            length=9
        )
        self.fields.append(self.B100_02)

        self.B100_03 = Element(
            name="B100_03",
            json_name="transactions_number",
            numeric=True,
            length=10
        )
        self.fields.append(self.B100_03)

        self.B100_04 = Element(
            name="B100_04",
            json_name="transactions_row_number",
            numeric=True,
            length=5
        )
        self.fields.append(self.B100_04)

        self.B100_05 = Element(
            name="B100_05",
            json_name="batch",
            numeric=True,
            length=8
        )
        self.fields.append(self.B100_05)

        self.B100_06 = Element(
            name="B100_06",
            json_name="transactions_type",
            numeric=False,
            length=15
        )
        self.fields.append(self.B100_06)

        self.B100_07 = Element(
            name="B100_07",
            json_name="reference",
            numeric=False,
            length=20
        )
        self.fields.append(self.B100_07)

        self.B100_08 = Element(
            name="B100_08",
            json_name="reference_document_type",
            numeric=True,
            length=3
        )
        self.fields.append(self.B100_08)

        self.B100_09 = Element(
            name="B100_09",
            json_name="reference2",
            numeric=False,
            length=20
        )
        self.fields.append(self.B100_09)

        self.B100_10 = Element(
            name="B100_10",
            json_name="reference_document_type2",
            numeric=True,
            length=3
        )
        self.fields.append(self.B100_10)

        self.B100_11 = Element(
            name="B100_11",
            json_name="details",
            numeric=False,
            length=50
        )
        self.fields.append(self.B100_11)

        self.B100_12 = Element(
            name="B100_12",
            json_name="date",
            numeric=True,
            length=8
        )
        self.fields.append(self.B100_12)

        self.B100_13 = Element(
            name="B100_13",
            json_name="value_date",
            numeric=True,
            length=8
        )
        self.fields.append(self.B100_13)

        self.B100_14 = Element(
            name="B100_14",
            json_name="transacting_account",
            numeric=False,
            length=15
        )
        self.fields.append(self.B100_14)

        self.B100_15 = Element(
            name="B100_15",
            json_name="counter_account",
            numeric=False,
            length=15
        )
        self.fields.append(self.B100_15)

        self.B100_16 = Element(
            name="B100_16",
            json_name="transaction_code",
            numeric=True,
            length=1
        )
        self.fields.append(self.B100_16)

        self.B100_17 = Element(
            name="B100_17",
            json_name="foreign_currency_code",
            numeric=False,
            length=3
        )
        self.fields.append(self.B100_17)

        self.B100_18 = Element(
            name="B100_18",
            json_name="transaction_amount",
            numeric=False,
            decimal=2,
            length=15
        )
        self.fields.append(self.B100_18)

        self.B100_19 = Element(
            name="B100_19",
            json_name="foreign_currency_amount",
            numeric=False,
            decimal=2,
            length=15
        )
        self.fields.append(self.B100_19)

        self.B100_20 = Element(
            name="B100_20",
            json_name="quantity_field",
            numeric=False,
            decimal=2,
            length=12
        )
        self.fields.append(self.B100_20)

        self.B100_21 = Element(
            name="B100_21",
            json_name="adjustment_field1",
            numeric=False,
            length=10
        )
        self.fields.append(self.B100_21)

        self.B100_22 = Element(
            name="B100_22",
            json_name="adjustment_field2",
            numeric=False,
            length=10
        )
        self.fields.append(self.B100_22)

        self.B100_24 = Element(
            name="B100_24",
            json_name="branch_id",
            numeric=False,
            length=7
        )
        self.fields.append(self.B100_24)

        self.B100_25 = Element(
            name="B100_25",
            json_name="order_date",
            numeric=True,
            length=8
        )
        self.fields.append(self.B100_25)

        self.B100_26 = Element(
            name="B100_26",
            json_name="user",
            numeric=False,
            length=9
        )
        self.fields.append(self.B100_26)

        self.B100_27 = Element(
            name="B100_27",
            numeric=False,
            length=25
        )
        self.fields.append(self.B100_27)

        self.field_count = len(self.fields) - 1


class B110(Segment):
    def __init__(self):
        Segment.__init__(self)

        self.id = Element(
            name="B110",
            content="B110",
        )
        self.fields.append(self.id)

        self.B110_01 = Element(
            name="B110_01",
            json_name="counter",
            numeric=True,
            length=9
        )
        self.fields.append(self.B110_01)

        self.B110_02 = Element(
            name="B110_02",
            json_name="authorized_dealer_number",
            numeric=True,
            length=9
        )
        self.fields.append(self.B110_02)

        self.B110_03 = Element(
            name="B110_03",
            json_name="account_code",
            numeric=False,
            length=15
        )
        self.fields.append(self.B110_03)

        self.B110_04 = Element(
            name="B110_04",
            json_name="account_name",
            numeric=False,
            length=50
        )
        self.fields.append(self.B110_04)

        self.B110_05 = Element(
            name="B110_05",
            json_name="test_balance_code",
            numeric=False,
            length=15
        )
        self.fields.append(self.B110_05)

        self.B110_06 = Element(
            name="B110_06",
            json_name="description_of_test_balance_code",
            numeric=False,
            length=30
        )
        self.fields.append(self.B110_06)

        self.B110_07 = Element(
            name="B110_07",
            json_name="client_supplier_street",
            numeric=False,
            length=50
        )
        self.fields.append(self.B110_07)

        self.B110_08 = Element(
            name="B110_08",
            json_name="customer_supplier_street2",
            numeric=False,
            length=10
        )
        self.fields.append(self.B110_08)

        self.B110_09 = Element(
            name="B110_09",
            json_name="customer_supplier_address_city",
            numeric=False,
            length=30
        )
        self.fields.append(self.B110_09)

        self.B110_10 = Element(
            name="B110_10",
            json_name="customer_supplier_address_zip",
            numeric=False,
            length=8
        )
        self.fields.append(self.B110_10)

        self.B110_11 = Element(
            name="B110_11",
            json_name="customer_supplier_address_country",
            numeric=False,
            length=30
        )
        self.fields.append(self.B110_11)

        self.B110_12 = Element(
            name="B110_12",
            json_name="country_code",
            numeric=False,
            length=2
        )
        self.fields.append(self.B110_12)

        self.B110_13 = Element(
            name="B110_13",
            json_name="Summary_account",
            numeric=False,
            length=15
        )
        self.fields.append(self.B110_13)

        self.B110_14 = Element(
            name="B110_14",
            json_name="beginning_balance",
            numeric=False,
            decimal=2,
            length=15
        )
        self.fields.append(self.B110_14)

        self.B110_15 = Element(
            name="B110_15",
            json_name="total_debit",
            numeric=False,
            decimal=2,
            length=15
        )
        self.fields.append(self.B110_15)

        self.B110_16 = Element(
            name="B110_16",
            json_name="total_credit",
            numeric=False,
            decimal=2,
            length=15
        )
        self.fields.append(self.B110_16)

        self.B110_17 = Element(
            name="B110_17",
            json_name="accounting_classification_code",
            numeric=True,
            length=4
        )
        self.fields.append(self.B110_17)

        self.B110_19 = Element(
            name="B110_19",
            json_name="supplier_customer_dealer_no",
            numeric=True,
            length=9
        )
        self.fields.append(self.B110_19)

        self.B110_21 = Element(
            name="B110_21",
            json_name="branch_id",
            numeric=False,
            length=7
        )
        self.fields.append(self.B110_21)

        self.B110_22 = Element(
            name="B110_22",
            json_name="beginning_bal_foreign_currency",
            numeric=False,
            decimal=2,
            length=15
        )
        self.fields.append(self.B110_22)

        self.B110_23 = Element(
            name="B110_23",
            json_name="curr_code_acc_balance_at_opp_cutoff",
            numeric=False,
            length=3
        )
        self.fields.append(self.B110_23)

        self.B110_24 = Element(
            name="B110_24",
            numeric=False,
            length=16
        )
        self.fields.append(self.B110_24)

        self.field_count = len(self.fields) - 1


class M100(Segment):
    def __init__(self):
        Segment.__init__(self)

        self.id = Element(
            name="M100",
            content="M100",
        )
        self.fields.append(self.id)

        self.M100_01 = Element(
            name="M100_01",
            json_name="counter",
            numeric=True,
            length=9
        )
        self.fields.append(self.M100_01)

        self.M100_02 = Element(
            name="M100_02",
            json_name="authorized_dealer_number",
            numeric=True,
            length=9
        )
        self.fields.append(self.M100_02)

        self.M100_03 = Element(
            name="M100_03",
            json_name="universal_catalog_number",
            numeric=False,
            length=20
        )
        self.fields.append(self.M100_03)

        self.M100_04 = Element(
            name="M100_04",
            json_name="supplier_manufacturer_catalog_number",
            numeric=False,
            length=20
        )
        self.fields.append(self.M100_04)

        self.M100_05 = Element(
            name="M100_05",
            json_name="internal_catalog_number",
            numeric=False,
            length=20
        )
        self.fields.append(self.M100_05)

        self.M100_06 = Element(
            name="M100_06",
            json_name="item_name",
            numeric=False,
            length=50
        )
        self.fields.append(self.M100_06)

        self.M100_07 = Element(
            name="M100_07",
            json_name="class_code",
            numeric=False,
            length=10
        )
        self.fields.append(self.M100_07)

        self.M100_08 = Element(
            name="M100_08",
            json_name="class_code_description",
            numeric=False,
            length=30
        )
        self.fields.append(self.M100_08)

        self.M100_09 = Element(
            name="M100_09",
            json_name="uom",
            numeric=False,
            length=20
        )
        self.fields.append(self.M100_09)

        self.M100_10 = Element(
            name="M100_10",
            json_name="item_balance_at_the_beginning",
            numeric=False,
            decimal=2,
            length=12
        )
        self.fields.append(self.M100_10)

        self.M100_11 = Element(
            name="M100_11",
            json_name="total_inventory_increase",
            numeric=False,
            decimal=2,
            length=12
        )
        self.fields.append(self.M100_11)

        self.M100_12 = Element(
            name="M100_12",
            json_name="total_inventory_decrease",
            numeric=False,
            decimal=2,
            length=12
        )
        self.fields.append(self.M100_12)

        self.M100_13 = Element(
            name="M100_13",
            json_name="cost_price_inventory_out_cut_off",
            numeric=True,
            decimal=2,
            length=10
        )
        self.fields.append(self.M100_13)

        self.M100_14 = Element(
            name="M100_14",
            json_name="cost_price_inventory_in_cut_off",
            numeric=True,
            decimal=2,
            length=10
        )
        self.fields.append(self.M100_14)

        self.M100_15 = Element(
            name="M100_15",
            numeric=False,
            length=50
        )
        self.fields.append(self.M100_15)

        self.field_count = len(self.fields) - 1

