import re


class CalcHelper:
    def __init__(self, journal):
        self.journal = journal
        self.name = (re.sub(r'^\w+\s*', '', journal.name).replace("/20", "")
                     .replace("/", "")
                     .replace("-D", "")
                     .replace("-1", ""))
        self.move_type = journal.move_type
        self.amount_tax = journal.amount_tax
        self.sale_order_count = journal.sale_order_count
        self.purchase_order_count = journal.purchase_order_count
        self.payment_state = journal.payment_state
        self.amount_total = journal.amount_total
        self.is_withholding = journal.is_withholding
        self.partner_id = journal.partner_id
        self.payment_id = journal.origin_payment_id
