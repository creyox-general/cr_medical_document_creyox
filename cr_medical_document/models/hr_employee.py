# -*- coding: utf-8 -*-
# Part of Creyox Technologies

from odoo import fields, models, api, _
from datetime import date, timedelta, datetime


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    medical_id = fields.One2many('medical.certificate', 'employee_id', string="Certificates")

    @api.model
    def send_certificate_reminders(self):
        today = date.today()
        reminder_date = today + timedelta(days=60)  # 2 months approx

        # Get certificates expiring exactly in 2 months
        certificates = self.env["medical.certificate"].search([
            ("expiration_date", ">=", datetime.combine(reminder_date, datetime.min.time())),
            ("expiration_date", "<", datetime.combine(reminder_date, datetime.max.time())),
        ])

        template = self.env.ref("cr_medical_document.email_template_certificate_reminder", raise_if_not_found=False)

        if template:
            for cert in certificates:
                if cert.employee_id and cert.employee_id.work_email:
                    template.with_context({
                        "certificate": cert,
                    }).send_mail(cert.employee_id.id, force_send=True)