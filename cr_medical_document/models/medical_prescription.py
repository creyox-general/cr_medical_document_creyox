# -*- coding: utf-8 -*-
# Part of Creyox Technologies

from odoo import fields, models, api, _


class MedicalPrescription(models.Model):
    _name = "medical.prescription"
    _description = "Medical Prescription"

    medical_document_id = fields.Many2one('medical.record', string="Medical Document")
    medication_name = fields.Selection(
        [("acamol", "Acamol"), ("advil", "Advil"), ("ventolin", "Ventolin"), ("breo_ellipta", "BREO ELLIPTA")],
        string="Medication Name")
    medicine_does = fields.Float(string="Does")
    medicine_does_unit = fields.Selection(
        [("mg", "MG"), ("mcg", "MCG"), ("g", "G"), ("drop", "Drop"), ("iu", "LU"), ("tab", "Tab"), ("ml", "ML")],
        string="Does Unit")
    route = fields.Selection(
        [("po", "PO"), ("inh", "INH"), ("top", "TOP"), ("io", "IO"), ("sc", "SC"), ("im", "IM"), ("iv", "IV"),
         ("pv", "PV"),
         ("pr", "PR")], string="Route")
    frequency = fields.Integer(string="Frequency")
    frequency_unit = fields.Selection(
        [("prn", "PRN"), ("day", "Day"), ("alt", "ALT"), ("days", "Days"), ("week", "Week"), ("month", "Month")],
        string="Frequency Unit")
    duration = fields.Integer(string="Duration")
    duration_unit = fields.Selection(
        [("day", "Day"), ("week", "Week"), ("month", "Month"), ("year", "Year")],
        string="Duration Unit")
    comment = fields.Char(string="Comment")