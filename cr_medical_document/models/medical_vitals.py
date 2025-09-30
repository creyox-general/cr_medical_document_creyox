# -*- coding: utf-8 -*-
# Part of Creyox Technologies

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class MedicalVitals(models.Model):
    _name = "medical.vitals"
    _description = "Medical Vitals"

    medical_document_id = fields.Many2one('medical.record', string="Medical Document")
    item = fields.Many2one('medical.vitals.items', string="Item")
    value = fields.Float("Value")
    unit = fields.Many2one(
        'medical.vitals.unit',
        string="Units",
        related="item.unit_id",
        store=True,
        readonly=True
    )
    min_range = fields.Char(related="item.min_range", string="Minimum Range")
    max_range = fields.Char(related="item.max_range", string="Maximum Range")
    sequence = fields.Integer("Sequence", default=1)

    def _check_value_range(self, vals=None):
        """Validate that value is within min_range and max_range"""
        for rec in self:
            val = rec.value
            if vals and 'value' in vals:
                val = vals['value']

            # Get min and max as floats
            try:
                min_val = float(rec.min_range) if rec.min_range else None
                max_val = float(rec.max_range) if rec.max_range else None
            except:
                raise ValidationError(
                    _("Invalid min_range or max_range format for vital '%s'. Must be a number.") % rec.item.name
                )

            # Check if value is outside range
            if min_val is not None and val < min_val:
                raise ValidationError(
                    _("Value %.2f is less than the minimum allowed %.2f for vital '%s'.") % (
                        val, min_val, rec.item.name
                    )
                )
            if max_val is not None and val > max_val:
                raise ValidationError(
                    _("Value %.2f is greater than the maximum allowed %.2f for vital '%s'.") % (
                        val, max_val, rec.item.name
                    )
                )

    def create(self, vals):
        record = super(MedicalVitals, self).create(vals)
        record._check_value_range(vals)
        return record

    def write(self, vals):
        res = super(MedicalVitals, self).write(vals)
        self._check_value_range(vals)
        return res