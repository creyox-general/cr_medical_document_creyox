# -*- coding: utf-8 -*-
# Copyright ...
# All Rights Reserved

from odoo import http
from odoo.http import request
import json
import re
import logging
from datetime import datetime
import pytz

ISRAEL_TZ = pytz.timezone('Asia/Jerusalem')  # Israel timezone

_logger = logging.getLogger(__name__)


def normalize_phone(number):
    """Normalize phone numbers to international format (972...)"""
    if not number:
        return ''
    num = re.sub(r'\D', '', number)  # keep only digits
    if num.startswith('972'):
        return num
    elif num.startswith('0'):  # local format like 0542126377
        return '972' + num[1:]
    elif len(num) == 9:  # short mobile format like 542126377
        return '972' + num
    return num


class PartnerCallHistoryController(http.Controller):
    """Public endpoint to log incoming partner call history records."""

    @http.route('/partner/call/history', type='http', auth="public", methods=['GET', 'POST'], csrf=False)
    def partner_call_history(self, **data):
        _logger.info("[CallHistory] Incoming request with data: %s", data)

        if request.httprequest.method == 'POST':
            try:
                raw_data = request.httprequest.data
                post_data = json.loads(raw_data.decode('utf-8'))
                _logger.info("[CallHistory] Parsed JSON data: %s", post_data)

                caller = post_data.get('caller')
                target = post_data.get('target')
                did = post_data.get('did')
                call_id = post_data.get('ivruniqueid')

                if not call_id:
                    raise ValueError("Missing call ID")

                # Prevent duplicate entry
                existing = request.env['partner.call.history'].sudo().search([('call_id', '=', call_id)], limit=1)
                if existing:
                    _logger.info(f"[CallHistory] Skipping duplicate call ID: {call_id}")
                    return json.dumps({'result': {'success': True, 'status': 'OK', 'message': 'Duplicate skipped', 'code': 200}})

                # Build partner map (only phone field)
                partners = request.env['res.partner'].sudo().search([('phone', '!=', False)])
                partner_map = {}
                for partner in partners:
                    if partner.phone:
                        num = normalize_phone(partner.phone)
                        if num:
                            partner_map.setdefault(num, []).append(partner.id)

                found_partner_ids = []

                # 1. Match by caller
                if caller:
                    normalized_caller = normalize_phone(caller)
                    found_partner_ids += partner_map.get(normalized_caller, [])

                # 2. Match by target
                if target:
                    normalized_target = normalize_phone(target)
                    if normalized_target.isdigit():
                        found_partner_ids += partner_map.get(normalized_target, [])
                    else:
                        # 3. If target is empty or non-numeric → fallback to DID
                        if did:
                            normalized_did = normalize_phone(did)
                            found_partner_ids += partner_map.get(normalized_did, [])

                found_partner_ids = list(set(found_partner_ids))  # unique partners

                call_time = None
                if post_data.get('time'):
                    utc_time = datetime.fromtimestamp(post_data['time'],
                                                      tz=pytz.utc)
                    israel_time = utc_time.astimezone(ISRAEL_TZ)
                    call_time = israel_time.replace(
                        tzinfo=None)  # naive for Odoo

                vals = {
                    'partner_ids': [(6, 0, found_partner_ids)] if found_partner_ids else False,
                    'did': did,
                    'caller': caller,
                    'target': target,
                    'callerextension': post_data.get('callerextension'),
                    'status': post_data.get('status'),
                    'type': post_data.get('type'),
                    'targetextension': post_data.get('targetextension'),
                    'department_name': post_data.get('DepartmentName'),
                    'representative_name': post_data.get('representative_name'),
                    'duration': post_data.get('duration'),
                    'call_id': call_id,
                    'record': post_data.get('record'),
                }

                call_entry = request.env['partner.call.history'].sudo().create(vals)
                call_entry.time = call_entry.create_date
                _logger.info("[CallHistory] Created entry ID: %s with partners %s", call_entry.id, found_partner_ids)

                return json.dumps({'result': {'success': True, 'status': 'OK', 'message': 'Call history created', 'code': 200}})

            except Exception as e:
                _logger.exception("[CallHistory] Error processing request: %s", e)
                return json.dumps({'result': {'success': False, 'status': 'ERROR', 'message': str(e), 'code': 500}})

        return json.dumps({'result': {'success': False, 'status': 'ERROR', 'message': 'Invalid request method', 'code': 405}})
