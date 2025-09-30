# -*- coding: utf-8 -*-
# Part of Creyox Technologies

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class SearchDetailsWizard(models.TransientModel):
    _name = "search.details.wizard"
    _description = "Search Medical Records Details"

    partner_id = fields.Many2one('res.partner', string="Patient", required=True)
    record_ids = fields.Many2many('medical.record', string="Medical Records")
    selected_record_id = fields.Many2one('medical.record', string="Select Record to Copy")

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
        if not self.selected_record_id:
            raise UserError("Please select a record to copy.")

        # Copy fields from selected record
        vals = {
            'partner_id': self.selected_record_id.partner_id.id,
            'date_time': self.selected_record_id.date_time,
            'visit_type': self.selected_record_id.visit_type,
            'therapist_id': self.selected_record_id.therapist_id.id,
            # add any other fields you want to copy
        }
        new_record = self.env['medical.record'].create(vals)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Medical Record',
            'res_model': 'medical.record',
            'view_mode': 'form',
            'res_id': new_record.id,
            'target': 'current',
        }
