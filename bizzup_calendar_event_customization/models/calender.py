from odoo import models, fields, api
from odoo.exceptions import UserError


class RoomBooking(models.Model):
    _inherit = "room.booking"

    calender_event_id = fields.Many2one('calendar.event', string="Calendar Event")

    def write(self, values):
        """
        Override the write method to synchronize relevant changes to the linked calendar event.

        If key fields (name, start/stop datetime, organizer, room) are updated,
        then the corresponding fields on the associated calendar event are also updated.
        """
        result = super().write(values)

        if self.env.context.get('skip_calendar_update'):
            return result

        sync_fields = {'start_datetime', 'stop_datetime', 'organizer_id', 'room_id', 'name'}
        if sync_fields.intersection(values) and self.calender_event_id:
            self.calender_event_id.with_context(skip_room_update=True).write({
                'name': self.name,
                'start': self.start_datetime,
                'stop': self.stop_datetime,
                'x_studio_many2one_field_22c_1j0tl6nva': self.room_id.id,
                'user_id': self.organizer_id.id,
            })

        return result

    def unlink(self):
        """
        Override the unlink method to ensure that the linked calendar event is also deleted
        when a room booking is removed, avoiding recursion via context flag.
        """
        if not self.env.context.get('skip_calendar_unlink'):
            for rec in self:
                if rec.calender_event_id:
                    rec.calender_event_id.with_context(skip_room_unlink=True).unlink()
        return super().unlink()


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override the create method to generate a linked room booking record
        when a calendar event with a room selection is created.
        """
        events = super().create(vals_list)
        for event in events:
            if event.x_studio_many2one_field_22c_1j0tl6nva:
                self.env["room.booking"].sudo().create({
                    "name": event.name,
                    "calender_event_id": event.id,
                    "room_id": event.x_studio_many2one_field_22c_1j0tl6nva.id,
                    "start_datetime": event.start,
                    "stop_datetime": event.stop,
                })
        return events

    @api.onchange('x_studio_many2one_field_22c_1j0tl6nva', 'name', 'start', 'stop', 'user_id')
    def onchange_event(self):
        """
        Onchange method to sync calendar event details with the linked room booking.

        - If a room is selected and a related room booking exists, update it.
        - If a room is selected and no room booking exists, create one.
        - Uses context flags to prevent recursive updates.
        """
        if self.env.context.get('skip_room_update') or not self.x_studio_many2one_field_22c_1j0tl6nva:
            return

        RoomBooking = self.env["room.booking"].sudo()
        room_booking = RoomBooking.search([("calender_event_id", "=", self._origin.id)], limit=1)
        if not self.name:
            raise UserError('Please enter name.')
        booking_vals = {
            'name': self.name,
            'organizer_id': self.user_id.id if self.user_id else False,
            'start_datetime': self.start,
            'stop_datetime': self.stop,
            'room_id': self.x_studio_many2one_field_22c_1j0tl6nva.id
        }

        if room_booking:
            room_booking.with_context(skip_calendar_update=True).write(booking_vals)
        else:
            booking_vals['calender_event_id'] = self._origin.id
            RoomBooking.create(booking_vals)

    def unlink(self):
        """
        Override the unlink method to ensure that the linked room booking is also deleted
        when a calendar event is removed, avoiding recursion via context flag.
        """
        if not self.env.context.get('skip_room_unlink'):
            for rec in self:
                self.env["room.booking"].sudo().search([
                    ("calender_event_id", "=", rec.id),
                ]).with_context(skip_calendar_unlink=True).unlink()
        return super().unlink()
