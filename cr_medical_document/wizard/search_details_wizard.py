# -*- coding: utf-8 -*-
# Part of Creyox Technologies

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class SearchDetailsWizard(models.TransientModel):
    _name = "search.details.wizard"
    _description = "Search Medical Records Details"

    partner_id = fields.Many2one('res.partner', string="Patient", required=True)
    record_ids = fields.Many2many('medical.record', string="Medical Records")

    def default_get(self, fields_list):
        res = super(SearchDetailsWizard, self).default_get(fields_list)
        if self._context.get('active_id'):
            current_record = self.env['medical.record'].browse(self._context['active_id'])
            res['partner_id'] = current_record.partner_id.id
            # fetch past records for the partner, excluding current record
            past_records = self.env['medical.record'].search([
                ('partner_id', '=', current_record.partner_id.id),
                ('date_time', '<', fields.Datetime.now()),
                ('id', '!=', current_record.id)  # exclude current record
            ])
            res['record_ids'] = [(6, 0, past_records.ids)]
        return res

    def action_copy_details(self):
        """Copy only one selected medical.record if is_selected_record is checked"""
        self.ensure_one()

        # Filter selected records
        selected_records = self.record_ids.filtered(lambda r: r.is_selected_record)

        if not selected_records:
            raise UserError("Please select one record to copy.")
        if len(selected_records) > 1:
            raise UserError("You can only copy one record at a time. Please uncheck extra selections.")

        rec = selected_records[0]
        vals = {
            'partner_id': rec.partner_id.id,
            'date_time': rec.date_time,
            'visit_type': rec.visit_type,
            'therapist_id': rec.therapist_id.id,
            'kupat_holim': rec.kupat_holim,
            'privat_insurence': rec.privat_insurence,
            'patient_dob': rec.patient_dob,
            'gender': rec.gender,
            'last_visit': rec.last_visit,
            'history_of_visit': rec.history_of_visit,
            'note': rec.note,
            'visit_detail': rec.visit_detail,
            'recommendations': rec.recommendations,
            # handle many2many
            'medical_disease_ids': [(6, 0, rec.medical_disease_ids.ids)],
        }
        new_record = self.env['medical.record'].create(vals)

        # Always open form view since only one record can be copied
        return {
            'type': 'ir.actions.act_window',
            'name': 'Medical Record',
            'res_model': 'medical.record',
            'view_mode': 'form',
            'res_id': new_record.id,
            'target': 'current',
        }