import datetime
from uuid import uuid4

import pytz
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from event_booking.models import Event, Ticket
from companies.models import Company
from event_booking.schemas import UseTicketSchema, EventSchema, EventUserInformation

User = get_user_model()


class EventBookingTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.company = Company.objects.create(name="Test Company")
        self.user = User.objects.create_user(
            username="testuser",
            password="password",
            first_name="test",
            last_name="test",
        )
        self.user2 = User.objects.create_user(
            username="testuser2",
            password="password",
            first_name="test",
            last_name="test",
        )
        self.staff_user = User.objects.create_user(
            username="teststaffuser", password="password", is_staff=True
        )
        self.event = Event.objects.create(
            name="Test Event",
            description="Test Event Description",
            type="ce",
            location="Test Location",
            company=self.company,
            release_time=timezone.now()
            - datetime.timedelta(days=1),  # So they have been released
            start_time=timezone.now() + datetime.timedelta(days=9),
            end_time=timezone.now() + datetime.timedelta(days=11),
            visible_time=timezone.now() - datetime.timedelta(days=9),
            capacity=100,
        )

    def _get_auth_headers(self, user: User) -> dict:
        """Generate JWT token for the user."""
        return {"Authorization": user.create_jwt_token()}

    def test_event_creation(self):
        self.assertEqual(self.event.name, "Test Event")
        self.assertEqual(self.event.capacity, 100)

    def test_ticket_creation(self):
        self.ticket = Ticket.objects.create(user=self.user, event=self.event)
        self.assertIsNotNone(self.ticket.user)
        self.assertIsNotNone(self.ticket.event)
        self.assertFalse(self.ticket.used)

    def test_get_events(self):
        headers = self._get_auth_headers(self.user)
        response = self.client.get("/api/events", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)  # Only one event exists

    def test_get_event(self):
        headers = self._get_auth_headers(self.user)
        response = self.client.get(f"/api/events/{self.event.id}/", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Test Event")

    def test_book_event(self):
        headers = self._get_auth_headers(self.user)
        response = self.client.post(
            f"/api/events/acquire-ticket/{self.event.id}", headers=headers
        )
        self.assertEqual(response.status_code, 200)
        self.event.refresh_from_db()
        self.assertEqual(self.event.number_booked, 1)

    def test_booked_events(self):
        headers = self._get_auth_headers(self.user)
        response = self.client.post(
            f"/api/events/acquire-ticket/{self.event.id}", headers=headers
        )
        self.assertEqual(response.status_code, 200)

        r2 = self.client.get("/api/events/booked-events", headers=headers)
        self.assertEqual(r2.status_code, 200)
        result: list[EventSchema] = [EventSchema(**event) for event in r2.json()]
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, self.event.id)

    def test_unbook_event(self):
        headers = self._get_auth_headers(self.user)
        Ticket.objects.create(user=self.user, event=self.event)
        self.event.number_booked += 1
        self.event.save()
        response = self.client.post(
            f"/api/events/remove-ticket/{self.event.id}", headers=headers
        )
        self.assertEqual(response.status_code, 200)
        self.event.refresh_from_db()
        self.assertEqual(self.event.number_booked, 0)

    def test_book_unreleased_event(self):
        self.event.release_time = timezone.now() + datetime.timedelta(days=1)
        self.event.save()
        headers = self._get_auth_headers(self.user)
        response = self.client.post(
            f"/api/events/acquire-ticket/{self.event.id}", headers=headers
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), "Event not yet released")

    def test_book_unset_release_event(self):
        self.event.release_time = None
        self.event.save()
        headers = self._get_auth_headers(self.user)
        response = self.client.post(
            f"/api/events/acquire-ticket/{self.event.id}", headers=headers
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), "Event release date not yet scheduled")

    def test_use_ticket(self):
        headers = self._get_auth_headers(self.user)
        self.ticket = Ticket.objects.create(user=self.user, event=self.event)
        response = self.client.post(
            "/api/events/use-ticket",
            data=UseTicketSchema(
                uuid=self.ticket.uuid, event_id=self.event.id
            ).model_dump(),
            content_type="application/json",
            headers=headers,
        )
        self.assertEqual(response.status_code, 401)
        response = self.client.post(
            "/api/events/use-ticket",
            data=UseTicketSchema(
                uuid=self.ticket.uuid, event_id=self.event.id
            ).model_dump(),
            content_type="application/json",
            headers=self._get_auth_headers(self.staff_user),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["used"], True)
        self.ticket.refresh_from_db()
        self.assertTrue(self.ticket.used)

    def test_nonexistent_ticket(self):
        response = self.client.post(
            "/api/events/use-ticket",
            data=UseTicketSchema(uuid=uuid4(), event_id=self.event.id).model_dump(),
            content_type="application/json",
            headers=self._get_auth_headers(self.staff_user),
        )
        self.assertEqual(response.status_code, 404)

    def test_book_event_twice(self):
        headers = self._get_auth_headers(self.user)
        self.client.post(f"/api/events/acquire-ticket/{self.event.id}", headers=headers)
        response = self.client.post(
            f"/api/events/acquire-ticket/{self.event.id}", headers=headers
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), "You have already booked this event")

    def test_unbook_without_booking(self):
        headers = self._get_auth_headers(self.user)
        response = self.client.post(
            f"/api/events/remove-ticket/{self.event.id}", headers=headers
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), "You do not have a ticket for this event")

    def test_book_fully_booked_event(self):
        self.event.capacity = 1
        self.event.number_booked = 1
        self.event.save()
        headers = self._get_auth_headers(self.user)
        response = self.client.post(
            f"/api/events/acquire-ticket/{self.event.id}", headers=headers
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), "Event already fully booked")

    def test_ticket_cannot_be_used_twice(self):
        """Ensure a ticket cannot be verified more than once."""
        ticket = Ticket.objects.create(user=self.user, event=self.event)

        # First valid use by staff
        response = self.client.post(
            "/api/events/use-ticket",
            data=UseTicketSchema(uuid=ticket.uuid, event_id=self.event.id).model_dump(),
            content_type="application/json",
            headers=self._get_auth_headers(self.staff_user),
        )
        self.assertEqual(response.status_code, 200)
        ticket.refresh_from_db()
        self.assertTrue(ticket.used)

        # Try using it again
        response = self.client.post(
            "/api/events/use-ticket",
            data=UseTicketSchema(uuid=ticket.uuid, event_id=self.event.id).model_dump(),
            content_type="application/json",
            headers=self._get_auth_headers(self.staff_user),
        )
        self.assertEqual(response.status_code, 404)  # Already used

    def test_ticket_invalid_for_different_event(self):
        """Ensure a ticket can only be used for the event it was issued for."""
        ticket = Ticket.objects.create(user=self.user, event=self.event)
        other_event = Event.objects.create(
            name="Another Event",
            description="Another event desc",
            type="ce",
            location="Other Location",
            company=self.company,
            start_time=timezone.now() + datetime.timedelta(days=3),
            end_time=timezone.now() + datetime.timedelta(days=4),
            capacity=50,
        )

        # Try to use the ticket for the wrong event
        response = self.client.post(
            "/api/events/use-ticket",
            data=UseTicketSchema(
                uuid=ticket.uuid, event_id=other_event.id
            ).model_dump(),
            content_type="application/json",
            headers=self._get_auth_headers(self.staff_user),
        )
        self.assertEqual(response.status_code, 404)

    def test_nonstaff_user_cannot_use_ticket_for_wrong_event(self):
        """Ensure non-staff users cannot use tickets, especially for the wrong event."""
        ticket = Ticket.objects.create(user=self.user, event=self.event)
        other_event = Event.objects.create(
            name="Other Event",
            description="Other event desc",
            type="ce",
            location="Somewhere else",
            company=self.company,
            start_time=timezone.now() + datetime.timedelta(days=5),
            end_time=timezone.now() + datetime.timedelta(days=6),
            capacity=20,
        )

        # Non-staff user tries to use ticket for the wrong event
        response = self.client.post(
            "/api/events/use-ticket",
            data=UseTicketSchema(
                uuid=ticket.uuid, event_id=other_event.id
            ).model_dump(),
            content_type="application/json",
            headers=self._get_auth_headers(self.user),  # not staff
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), "This route is staff only.")

    def test_unbook_used_ticket(self):
        """Ensure users cannot unbook tickets that have already been used."""
        headers = self._get_auth_headers(self.user)
        ticket = Ticket.objects.create(user=self.user, event=self.event)
        self.event.number_booked += 1
        self.event.save()

        # Staff user marks the ticket as used
        staff_headers = self._get_auth_headers(self.staff_user)
        response = self.client.post(
            "/api/events/use-ticket",
            data=UseTicketSchema(uuid=ticket.uuid, event_id=self.event.id).model_dump(),
            content_type="application/json",
            headers=staff_headers,
        )
        self.assertEqual(response.status_code, 200)

        # User tries to unbook the used ticket
        response = self.client.post(
            f"/api/events/remove-ticket/{self.event.id}", headers=headers
        )
        self.assertEqual(response.status_code, 404, response.content)
        self.assertEqual(response.json(), "You do not have a ticket for this event")
        self.event.refresh_from_db()
        self.assertEqual(self.event.number_booked, 1)

    def test_unbook_owned_ticket_past_unbook_limit(self):
        """Ensure users cannot unbook tickets past the unbooking limit."""
        self.event.start_time = timezone.now() + datetime.timedelta(hours=25)
        self.event.save()
        headers = self._get_auth_headers(self.user)
        Ticket.objects.create(user=self.user, event=self.event)
        self.event.number_booked += 1
        self.event.save()

        # User tries to unbook the ticket past the unbooking limit (7 days)
        response = self.client.post(
            f"/api/events/remove-ticket/{self.event.id}", headers=headers
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), "Unbooking period has expired")
        self.event.refresh_from_db()
        self.assertEqual(self.event.number_booked, 1)

    def test_get_events_not_visible(self):
        self.event.visible_time = timezone.now() + datetime.timedelta(days=1)
        self.event.save()
        headers = self._get_auth_headers(self.user)
        response = self.client.get("/api/events", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)  # No events should be visible

    def test_get_event_not_visible(self):
        self.event.visible_time = timezone.now() + datetime.timedelta(days=1)
        self.event.save()
        headers = self._get_auth_headers(self.user)
        response = self.client.get(f"/api/events/{self.event.id}/", headers=headers)
        self.assertEqual(response.status_code, 404)

    def test_acquire_ticket_after_deadline(self):
        self.event.release_time = timezone.now() - datetime.timedelta(days=10)
        self.event.start_time = timezone.now() + datetime.timedelta(days=1)
        self.event.end_time = timezone.now() + datetime.timedelta(days=2)
        self.event.save()
        headers = self._get_auth_headers(self.user)
        response = self.client.post(
            f"/api/events/acquire-ticket/{self.event.id}", headers=headers
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), "Booking period has expired")

    def test_get_events_returns_booking_freezes_at(self):
        # Helper function to parse ISO 8601 strings with 'Z' into timezone-aware datetime objects
        # This uses strptime for compatibility with Python < 3.7
        def parse_iso_z_compatible(iso_string):
            # 1. Handle the microsecond precision. strptime requires exact match for fractional seconds.
            #    We'll truncate the string to 6 decimal places (microseconds) if it has more.
            #    If it has fewer, strptime will still work, but we need to ensure the format string matches.
            if "." in iso_string:
                base, fractional_z = iso_string.split(".")
                fractional = fractional_z.rstrip("Z")
                # Truncate fractional seconds to 6 digits (microseconds) or pad with zeros
                fractional_padded = fractional.ljust(6, "0")[:6]
                string_to_parse = f"{base}.{fractional_padded}"
                format_string = "%Y-%m-%dT%H:%M:%S.%f"
            else:
                string_to_parse = iso_string.rstrip("Z")
                format_string = "%Y-%m-%dT%H:%M:%S"

            # 2. Parse the time string (it will be naive, without timezone info)
            naive_dt = datetime.datetime.strptime(string_to_parse, format_string)

            # 3. Attach the UTC timezone (since the original string ended in 'Z')
            return naive_dt.replace(tzinfo=pytz.utc)

        # 1. API Call and Initial Assertions
        headers = self._get_auth_headers(self.user)
        response = self.client.get("/api/events", headers=headers)
        self.assertEqual(response.status_code, 200)
        events = response.json()
        self.assertIn("bookingFreezesAt", events[0])

        # 2. Calculate the Expected Time
        # Ensure self.event.start_time is a timezone-aware datetime object
        expected_dt_object = (
            self.event.start_time - Event.booking_change_deadline_delta()
        )

        # We need to generate the ISO string to pass it to the parser,
        # as it will ensure microsecond precision is included if necessary.
        expected_freeze_time_str = expected_dt_object.isoformat().replace("+00:00", "Z")

        # 3. Get the Actual Time
        actual_freeze_time_str = events[0]["bookingFreezesAt"]

        # 4. Convert to Datetime Objects using the compatible parser
        try:
            actual_dt = parse_iso_z_compatible(actual_freeze_time_str)
            expected_dt = parse_iso_z_compatible(expected_freeze_time_str)
        except ValueError as e:
            self.fail(
                f"Could not parse datetime strings using strptime: {e}. "
                f"Actual: '{actual_freeze_time_str}', Expected: '{expected_freeze_time_str}'"
            )

        # 5. Define Tolerance (1 second)
        tolerance = datetime.timedelta(seconds=1)

        # 6. Assert the Difference is Within Tolerance
        time_difference = abs(actual_dt - expected_dt)

        self.assertTrue(
            time_difference < tolerance,
            msg=f"Booking freeze times are not within {tolerance}. "
            f"Difference: {time_difference}. "
            f"Expected: {expected_dt}, Actual: {actual_dt}",
        )

    def test_get_attending_information_non_staff_user(self):
        headers = self._get_auth_headers(self.user)
        response = self.client.get(
            f"/api/events/{self.event.id}/attending", headers=headers
        )
        self.assertEqual(response.status_code, 401)

    def test_get_attending_information_staff_user(self):
        headers = self._get_auth_headers(self.staff_user)
        Ticket.objects.create(user=self.user, event=self.event, used=True)
        Ticket.objects.create(user=self.user2, event=self.event)
        response = self.client.get(
            f"/api/events/{self.event.id}/attending", headers=headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

        result: list[EventUserInformation] = [
            EventUserInformation(**event) for event in response.json()
        ]
        # Look through ids and find the ones for the different users
        user1_info = next(
            (info for info in result if info.user_id == self.user.id), None
        )
        user2_info = next(
            (info for info in result if info.user_id == self.user2.id), None
        )
        self.assertIsNotNone(user1_info)
        self.assertIsNotNone(user2_info)
        self.assertTrue(user1_info.ticket_used)
        self.assertFalse(user2_info.ticket_used)
