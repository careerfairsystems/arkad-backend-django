import datetime

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from event_booking.models import Event, Ticket
from companies.models import Company

User = get_user_model()

class EventBookingTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.company = Company.objects.create(name="Test Company")
        self.user = User.objects.create_user(username="testuser", password="password")
        self.event = Event.objects.create(
            name="Test Event",
            description="Test Event Description",
            type="ce",
            location="Test Location",
            company=self.company,
            start_time=timezone.now() + datetime.timedelta(days=1),
            end_time=timezone.now() + datetime.timedelta(days=2),
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
        response = self.client.post(f"/api/events/{self.event.id}/book", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.event.refresh_from_db()
        self.assertEqual(self.event.number_booked, 1)

    def test_unbook_event(self):
        headers = self._get_auth_headers(self.user)
        Ticket.objects.create(user=self.user, event=self.event)
        self.event.number_booked += 1
        self.event.save()
        response = self.client.post(f"/api/events/{self.event.id}/unbook", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.event.refresh_from_db()
        self.assertEqual(self.event.number_booked, 0)

    def test_use_ticket(self):
        headers = self._get_auth_headers(self.user)
        self.ticket = Ticket.objects.create(user=self.user, event=self.event)
        response = self.client.post("/api/events/use-ticket", {"uuid": str(self.ticket.uuid)}, headers=headers)
        print(response.content)
        self.assertEqual(response.status_code, 200)
        self.ticket.refresh_from_db()
        self.assertTrue(self.ticket.used)

    def test_book_event_twice(self):
        headers = self._get_auth_headers(self.user)
        self.client.post(f"/api/events/{self.event.id}/book", headers=headers)
        response = self.client.post(f"/api/events/{self.event.id}/book", headers=headers)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), "You have already booked this event")

    def test_unbook_without_booking(self):
        headers = self._get_auth_headers(self.user)
        response = self.client.post(f"/api/events/{self.event.id}/unbook", headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), "You do not have a ticket for this event")

    def test_book_fully_booked_event(self):
        self.event.capacity = 1
        self.event.number_booked = 1
        self.event.save()
        headers = self._get_auth_headers(self.user)
        response = self.client.post(f"/api/events/{self.event.id}/book", headers=headers)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), "Event already fully booked")
