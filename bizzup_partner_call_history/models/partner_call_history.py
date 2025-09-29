# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

import requests
import re
import logging
from datetime import datetime
from odoo import models, api,fields

_logger = logging.getLogger(__name__)

def normalize_phone(number):
    """Normalize phone numbers to international format (972...)"""
    if not number:
        return ''
    num = re.sub(r'\D', '', number)  # keep only digits
    if num.startswith('972'):
        return num
    elif num.startswith('0'):  # local format
        return '972' + num[1:]
    return num


class PartnerCallHistory(models.Model):
    """
    Model to store call history related to a partner (res.partner).
    Includes call metadata, representative info, and AI-generated summary.
    """
    _name = 'partner.call.history'
    _description = 'Partner Call History'

    partner_ids = fields.Many2many('res.partner', string='Partners')
    time = fields.Datetime(string='Call Time')
    did = fields.Char(string='DID')
    caller = fields.Char(string='Caller')
    target = fields.Char(string='Target')
    callerextension = fields.Char(string='Caller Extension')
    status = fields.Char(string='Status')
    type = fields.Char(string='Type')
    targetextension = fields.Char(string='Target Extension')
    department_name = fields.Char(string='Department Name')
    record = fields.Char(string='Record')
    representative_name = fields.Char(string='Representative Name')
    duration = fields.Float(string='Duration (seconds)')
    call_id = fields.Char(string="Call ID", index=True)


    @api.model
    def update_call_history(self):
        """Assign partner_ids to call history records based on phone number matching"""
        CallHistory = self.env['partner.call.history'].sudo()
        Partner = self.env['res.partner'].sudo()

        # Calls without partners
        unassigned_calls = CallHistory.search([('partner_ids', '=', False)])

        # Build partner map (only phone field)
        partners = Partner.search([('phone', '!=', False)])
        partner_map = {}
        for partner in partners:
            normalized_phone = normalize_phone(partner.phone)
            if normalized_phone:
                partner_map.setdefault(normalized_phone, []).append(partner.id)

        _logger.info("Partner map prepared with %s entries", len(partner_map))

        updated_calls = []

        for call in unassigned_calls:
            found_partner_ids = []

            # 1. Match by caller
            if call.caller:
                normalized_caller = normalize_phone(call.caller)
                found_partner_ids += partner_map.get(normalized_caller, [])

            # 2. Match by target (or fallback to DID if non-numeric / empty)
            target_to_use = call.target
            if not target_to_use or not target_to_use.isdigit():
                target_to_use = call.did

            if target_to_use:
                normalized_target = normalize_phone(target_to_use)
                found_partner_ids += partner_map.get(normalized_target, [])

            found_partner_ids = list(set(found_partner_ids))  # unique partners

            if found_partner_ids:
                call.partner_ids = [(6, 0, found_partner_ids)]
                updated_calls.append(call.id)
                _logger.info(
                    f"Updated Call {call.call_id} with partners {found_partner_ids}"
                )
            else:
                _logger.info(
                    f"No phone match for Call {call.call_id} "
                    f"(caller={call.caller}, target={call.target}, did={call.did})"
                )

        return updated_calls