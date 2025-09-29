# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class DepositsReportWizard(models.TransientModel):
    _name = "deposits.report.wizard"
    _description = "Deposits Report Wizard"

    depo_means_of_payment = fields.Selection([
        ('1', 'Cash'),
        ('2', 'Check')
    ], string="Means of Payment")
    start_date = fields.Date(
        string="Start Date",
        default=datetime.now().date().replace(month=1, day=1)
    )
    end_date = fields.Date(
        string="End Date",
        default=datetime.now().date().replace(month=12, day=31)
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    state = fields.Selection([
        ('choose', 'choose'),
        ('get', 'get')
    ], default='choose')
    deposite_data = fields.Binary(
        string='Deposite Report',
        readonly=True,
        attchment=False
    )
    deposite_filename = fields.Char()

    def generate_report(self):
        """This function will generate the values for the report and
        will generate the report when clicked on Generate Button."""
        data = {
            'model': 'account.payment',
            'form': self.read()[0],
        }
        start_date = self.start_date
        end_date = self.end_date
        means_of_payment = self.depo_means_of_payment
        if start_date > end_date:
            raise ValidationError(
                _("Please add valid dates. Start date cannot be greater than end date")
            )
        payments = self.env['account.payment'].search([
            ('means_of_payment', '=', means_of_payment),
            ('validity_date', '>=', start_date),
            ('validity_date', '<=', end_date),
            ('is_deposited', '!=', True),
            ('payment_type', '=', 'inbound'),
            ('is_refund', '=', False),
        ])
        docs = []
        if not payments:
            raise ValidationError(_("No Payments found in this period"))

        total = 0
        for rec in payments:
            total = total + rec.amount
            payments_data = {
                'validity_date': rec.validity_date,
                'subject_report': rec.receipt_id.subject,
                'name_report': rec.receipt_id.name,
                'check_payment_due_date': rec.check_payment_due_date,
                'bank_number': rec.bank_number,
                'branch_number': rec.branch_number,
                'account_number': rec.account_number,
                'amount': rec.amount,
            }
            docs.append(payments_data)
        docs.append({'total': total})
        data['docs_list'] = docs

        return self.env.ref('bizzup_deposite_report.deposite_report').report_action(self, data=data)
