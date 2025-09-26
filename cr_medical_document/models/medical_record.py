# -*- coding: utf-8 -*-
# Part of Creyox Technologies

from odoo import fields, models, api, _


class MedicalRecord(models.Model):
    _name = "medical.record"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Medical Record"

    name = fields.Char(string="Description")
    partner_id = fields.Many2one('res.partner', string="Patient", requied=True, tracking=True)
    patient_phone = fields.Char(related="partner_id.phone", string="Phone", readonly=False, tracking=True)
    partner_image = fields.Binary(related="partner_id.image_1920", string="Image")
    kupat_holim = fields.Selection(
        [("clalit", "Clalit"), ("maccabi", "Maccabi"), ("meuhedet", "Meuhedet"), ("leumit", "Leumit")],
        string="Kupat Holim")
    privat_insurence = fields.Char(string="Private Insurance")
    patient_dob = fields.Date(string="Birth Date", tracking=True)
    gender = fields.Selection(
        [("male", "Male"), ("female", "Female")],
        string="Gender", tracking=True)
    last_visit = fields.Boolean(string="Last Visit")
    history_of_visit = fields.Selection(
        [("1/1/2025", "1/1/2025"), ("2/1/2025", "2/1/2025"), ("3/1/2025", "3/1/2025")], string="History Of Visit")
    note = fields.Html(string="Note")
    therapist_id = fields.Many2one('res.users', string="Dr/ Therapist", tracking=True)
    visit_type = fields.Selection(
        [("consultation", "Consultation"), ("esthetics", "Esthetics"), ("procedure", "Procedure"),
         ("phone Call", "Phone Call"), ("administration", "Administration")], string="Visit Type")
    date_time = fields.Datetime(string="Date Time")
    pdf_count = fields.Float(string="PDF Count")
    schedule_followup_count = fields.Float(string="Schedule Follow-up Count")
    clinical_history_count = fields.Float(string="Clinical History Count")
    sequence = fields.Integer("Sequence", default=1)
    visit_detail = fields.Html(string="Visit Details")
    recommendations = fields.Html(string="Recommendations")
    medical_disease_ids = fields.Many2many('medical.disease', 'medical_document_id', string="Medical Disease")
    medical_vital_ids = fields.One2many('medical.vitals', 'medical_document_id', string="Medical Vitals")
    medical_prescription_ids = fields.One2many('medical.prescription', 'medical_document_id', string="Medical Prescription")
    medical_product_service_ids = fields.One2many('medical.product.service', 'medical_document_id', string="Medical Product Service")
    product_id = fields.Many2one('product.template', string="Product Name")
    product_quantity = fields.Float(string="Quantity")
    product_price = fields.Float(string="Price")
    total = fields.Float(string="Total")

    def action_pdf(self):
        pass

    def action_schedule_followup(self):
        pass

    def action_clinical_history(self):
        pass