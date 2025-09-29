# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

{
    "name": "Bizzup Calendar Event Customization",
    "version": "18.0.1.3.0",
    "description": """
        This module customizes the Calendar module to restrict attendee selection 
        to only those partners who are also employees. The filtering applies to both 
        the attendee dropdown list and the "Search More..." dialog when adding attendees 
        to a calendar event.
        HT01941 | When a user creates an appointment and selects a meeting room(which is already present studio field), 
                        the same room should automatically be booked in the meeting room calendar.
    """,
    "license": "Other proprietary",
    "author": "Gilliam Management Services and Information Systems, Ltd.",
    "depends": ["calendar", "hr"],
    "data": [],
    "assets": {
        'web.assets_backend': [
            'bizzup_calendar_event_customization/static/src/js/calendar_attendees_filter.js',
        ],
    },
    "installable": True,
    "auto_install": False,
}
