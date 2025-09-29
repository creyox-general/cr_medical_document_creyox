# -*- coding: utf-8 -*-
# Part of Creyox Technologies

from odoo import fields, models, api, _
from datetime import date, timedelta


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    medical_id = fields.One2many('medical.certificate', 'employee_id', string="Employee")

    def send_certificate_reminders(self):
        today = date.today()
        reminder_date = today + timedelta(days=60)  # 2 months approx

        for employee in self:
            for line in employee.medical_id:
                if line.expiration_date and line.expiration_date == reminder_date:
                    template = self.env.ref('cr_medical_document.email_template_certificate_reminder')
                    template.send_mail(employee.id, force_send=True)