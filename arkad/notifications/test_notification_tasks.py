import datetime
from datetime import timedelta  # ADDED: Required for timedelta usage throughout setUp
from unittest.mock import patch
import uuid

# Assume your model imports are available
from django.test import TestCase

# These imports reference the code the user provided (the tasks file)
from notifications import tasks

# Mock model imports (replace with your actual model imports)
# We assume these models are available in the test environment for creation
from event_booking.models import Event, Ticket
from student_sessions.models import (
    StudentSession,
    SessionType,
    StudentSessionTimeslot,
    StudentSessionApplication,
    ApplicationStatus,
)
from user_models.models import User
from notifications.models import Notification
from companies.models import Company

# Define constants used in assertions
MOCK_APP_BASE_URL = "https://example.com/app"
# MOCK_LOCAL_TIME_STR is 13:00 due to the mock_make_local_time implementation
MOCK_LOCAL_TIME_STR = "13:00"


# Mock implementation for make_local_time to return a predictable, formatted time.
def mock_make_local_time(dt: datetime.datetime) -> datetime.datetime:
    """Mock utility to return a predictable timezone-aware datetime."""
    # Ensure the returned time, when formatted in tasks, produces consistent output (13:00).
    # FIXED: Using datetime.timezone.utc which is available since 'import datetime' is present.
    return dt.replace(
        hour=13, minute=0, second=0, microsecond=0, tzinfo=datetime.timezone.utc
    )


class NotificationTasksTestCase(TestCase):
    """
    Tests for all notification Celery tasks defined in notifications.tasks.
    We assert on the creation and content of Notification objects, not on actual Celery scheduling.
    """

    def setUp(self) -> None:
        # 1. Setup Mock Time (Oct 10, 2025 @ 12:00 UTC)
        # FIXED: Using datetime.timezone.utc to resolve AttributeError
        self.mock_now = datetime.datetime(
            2025, 10, 10, 12, 0, tzinfo=datetime.timezone.utc
        )
        self.now_patcher = patch(
            "django.utils.timezone.now", return_value=self.mock_now
        )
        self.now_patcher.start()

        # 2. Setup Utility Mock (Used for time formatting in task bodies)
        self.make_local_time_patcher = patch(
            "notifications.tasks.make_local_time", side_effect=mock_make_local_time
        )
        self.make_local_time_patcher.start()

        # 3. Setup App Base URL Mock
        self.app_base_url_patcher = patch(
            "notifications.tasks.APP_BASE_URL", MOCK_APP_BASE_URL
        )
        self.app_base_url_patcher.start()

        # 4. Create Required Mock Data

        # Users
        self.user1 = User.objects.create(
            id=1,
            first_name="Alice",
            email="alice@test.com",
            username="alice@test.com",
            fcm_token="TEST_FCM_TOKEN",
        )
        self.user2 = User.objects.create(
            id=2,
            first_name="Bob",
            email="bob@test.com",
            username="bob@test.com",
            fcm_token="TEST_FCM_TOKEN_2",
        )
        self.user3 = User.objects.create(
            id=3,
            first_name="Charlie",
            email="charlie@test.com",
            username="charlie@test.com",
            fcm_token="TEST_FCM_TOKEN_3",
        )
        self.company = Company.objects.create(id=100, name="Test Company")

        # --- Event Setup ---
        self.event = Event.objects.create(
            id=1,
            name="Test Event",
            start_time=self.mock_now + timedelta(days=1, hours=1),
            end_time=self.mock_now + timedelta(days=1, hours=2),
            location="Test Location Hall A",
            capacity=100,
        )
        self.ticket1_uuid = uuid.uuid4()
        self.ticket1 = Ticket.objects.create(
            user=self.user1, event=self.event, used=False, uuid=self.ticket1_uuid
        )
        self.ticket_used = Ticket.objects.create(
            user=self.user2, event=self.event, used=True, uuid=uuid.uuid4()
        )
        self.ticket_used2 = Ticket.objects.create(
            user=self.user3, event=self.event, used=True, uuid=uuid.uuid4()
        )

        # --- Student Session Setup (Regular) ---
        self.ss_reg = StudentSession.objects.create(
            id=10,
            company=self.company,
            session_type=SessionType.REGULAR,
            disclaimer="Only Swedish citizens.",
            booking_open_time=self.mock_now + timedelta(days=1),
        )

        # Timeslot (30 min duration -> 13:00 to 13:30 local time in assertion)
        self.timeslot_reg = StudentSessionTimeslot.objects.create(
            id=1000,
            student_session=self.ss_reg,
            start_time=self.mock_now + timedelta(days=1, hours=1),
            duration=30,
            booking_closes_at=self.mock_now + timedelta(days=5),
        )

        # Application (Must be accepted for timeslot reminders)
        self.app_reg = StudentSessionApplication.objects.create(
            id=100,
            student_session=self.ss_reg,
            user=self.user1,
            status=ApplicationStatus.ACCEPTED,
        )
        # Link application to timeslot for test context
        self.timeslot_reg.selected_applications.add(self.app_reg)

        # --- Student Session Setup (Company Event) ---
        self.ss_event = StudentSession.objects.create(
            id=11,
            company=self.company,
            session_type=SessionType.COMPANY_EVENT,
            disclaimer=None,
            company_event_at=self.mock_now + timedelta(days=1, hours=1),
        )

    def tearDown(self) -> None:
        self.now_patcher.stop()
        self.make_local_time_patcher.stop()
        self.app_base_url_patcher.stop()

    # --- Event Task Tests ---

    def test_notify_event_tomorrow_success(self) -> None:
        """Tests 24-hour reminder for an active ticket with location."""
        tasks.notify_event_tomorrow(self.ticket1_uuid)

        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.get()

        # Check flags and target user
        self.assertTrue(notification.email_sent)
        self.assertTrue(notification.fcm_sent)
        self.assertEqual(notification.target_user, self.user1)

        # Prepare safe string fields
        title = notification.title or ""
        body = notification.body or ""
        email_body = notification.email_body or ""

        # Check content using dynamic data and key phrases
        self.assertIn(self.event.name, title)
        self.assertIn("Reminder:", title)

        self.assertIn(self.event.name, body)
        self.assertIn("tomorrow", body)
        self.assertIn(MOCK_LOCAL_TIME_STR, body)
        self.assertIn(self.event.location, body)

        self.assertIn(self.event.name, email_body)
        self.assertIn(self.event.location, email_body)
        self.assertIn("confirmed ticket", email_body)

        self.assertEqual(
            notification.button_link,
            f"{MOCK_APP_BASE_URL}/events/detail/{self.event.id}/ticket",
        )

    def test_notify_event_tomorrow_missing_ticket_or_used(self) -> None:
        """Tests that no notification is sent if the ticket is missing or used."""
        tasks.notify_event_tomorrow(uuid.uuid4())
        tasks.notify_event_tomorrow(self.ticket_used.uuid)
        self.assertEqual(Notification.objects.count(), 0)

    def test_notify_event_one_hour_success(self) -> None:
        """Tests 1-hour reminder for an active ticket (FCM only)."""
        tasks.notify_event_one_hour(self.ticket1_uuid)

        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.get()

        # Check flags
        self.assertFalse(notification.email_sent)
        self.assertTrue(notification.fcm_sent)
        self.assertIsNone(notification.email_body)

        # Prepare safe string fields
        title = notification.title or ""
        body = notification.body or ""

        # Check content using dynamic data and key phrases
        self.assertIn(self.event.name, title)
        self.assertIn("1 Hour!", title)
        self.assertIn("one hour", body)
        self.assertIn(MOCK_LOCAL_TIME_STR, body)
        self.assertIn(self.event.location, body)

    def test_notify_event_registration_open(self) -> None:
        """Tests the broadcast for event registration opening."""
        tasks.notify_event_registration_open(self.event.id)

        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.get()

        # Prepare safe string fields
        title = notification.title or ""
        body = notification.body or ""

        self.assertEqual(notification.notification_topic, "broadcast")
        self.assertIn("Registration Open:", title)
        self.assertIn(self.event.name, body)
        self.assertIn("now open!", body)
        self.assertFalse(notification.email_sent)

    def test_notify_event_registration_closes_tomorrow(self) -> None:
        """Tests unbooking reminder is sent to active ticket holders."""
        Ticket.objects.create(
            user=self.user2, event=self.event, used=False, uuid=uuid.uuid4()
        )

        tasks.notify_event_registration_closes_tomorrow(self.event.id)

        self.assertEqual(Notification.objects.count(), 2)
        notifications = Notification.objects.order_by("target_user__id")

        # Prepare safe string fields for each notification
        n0_title = notifications[0].title or ""
        n0_body = notifications[0].body or ""
        n0_email_body = notifications[0].email_body or ""
        n1_title = notifications[1].title or ""

        # Check notification for user1 (Alice)
        self.assertEqual(notifications[0].target_user, self.user1)
        self.assertTrue(notifications[0].email_sent)

        # Check content keywords
        self.assertIn("Unbooking for", n0_title)
        self.assertIn(self.event.name, n0_title)
        self.assertIn("closes tomorrow", n0_body)
        self.assertIn("unbook your ticket immediately", n0_email_body)

        # Check notification for user2 (Bob)
        self.assertEqual(notifications[1].target_user, self.user2)
        self.assertIn("Action Required:", n1_title)

        # Check that the used ticket holder did NOT receive a notification.
        self.assertNotIn(self.ticket_used2.user, [n.target_user for n in notifications])

    # --- Student Session Task Tests (REGULAR SESSION) ---

    def test_notify_student_session_tomorrow_regular(self) -> None:
        """Tests 24-hour reminder for a regular session with a disclaimer."""
        tasks.notify_student_session_tomorrow(
            self.user1.id, self.ss_reg.id, self.timeslot_reg.id
        )

        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.get()

        self.assertTrue(notification.email_sent)

        # Prepare safe string fields
        body = notification.body or ""
        title = notification.title or ""
        heading = notification.heading or ""
        email_body = notification.email_body or ""

        # Check time and disclaimer are included
        self.assertIn(MOCK_LOCAL_TIME_STR, body)
        self.assertIn(
            (self.ss_reg.disclaimer or "").split(".")[0], body
        )  # 'Only Swedish citizens'

        # Check session type naming
        self.assertIn("Student Session with Test Company", title)
        self.assertIn("Student Session Tomorrow", heading)

        # Check email body for disclaimer and time info
        self.assertIn(self.ss_reg.disclaimer or "", email_body)
        self.assertIn("confirmed timeslot", email_body)
        self.assertIn(self.company.name, email_body)

        self.assertEqual(
            notification.button_link,
            f"{MOCK_APP_BASE_URL}/sessions/book/{self.company.id}",
        )

    def test_notify_student_session_one_hour_regular(self) -> None:
        """Tests 1-hour reminder for a regular session (FCM only, with disclaimer)."""
        tasks.notify_student_session_one_hour(
            self.user1.id, self.ss_reg.id, self.timeslot_reg.id
        )

        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.get()

        self.assertFalse(notification.email_sent)

        # Prepare safe string fields
        title = notification.title or ""
        body = notification.body or ""

        # Check content keywords
        self.assertIn("1 Hour Notice:", title)
        self.assertIn("Student Session with Test Company", title)
        self.assertIn("starts in one hour", body)
        self.assertIn(MOCK_LOCAL_TIME_STR, body)
        self.assertIn((self.ss_reg.disclaimer or "").split(".")[0], body)

    # --- Student Session Task Tests (COMPANY EVENT) ---

    def test_notify_student_session_tomorrow_company_event(self) -> None:
        """Tests 24-hour reminder for a company event (no disclaimer)."""
        # Create a timeslot for the Company Event
        timeslot_event = StudentSessionTimeslot.objects.create(
            id=2000,
            student_session=self.ss_event,
            start_time=self.mock_now + timedelta(days=1, hours=1),
            duration=480,  # 8 hours
        )
        app_event = StudentSessionApplication.objects.create(
            id=200,
            student_session=self.ss_event,
            user=self.user2,
            status=ApplicationStatus.ACCEPTED,
        )
        timeslot_event.selected_applications.add(app_event)

        tasks.notify_student_session_tomorrow(
            self.user2.id, self.ss_event.id, timeslot_event.id
        )

        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.get()

        # Prepare safe string fields
        title = notification.title or ""
        heading = notification.heading or ""
        email_body = notification.email_body or ""
        body = notification.body or ""

        # Check session type naming
        self.assertIn("Company Event with Test Company", title)
        self.assertIn("Company Event Tomorrow", heading)
        self.assertIn("confirmed timeslot for a Company Event", email_body)

        # Check for missing disclaimer
        self.assertNotIn("disclaimer", body)
        self.assertNotIn("disclaimer", email_body)
        self.assertIn("13:00", body)

    # --- Booking Freeze Task Test ---

    def test_notify_student_session_timeslot_booking_freezes_tomorrow(self) -> None:
        """Tests the unbooking/freeze reminder for a regular session."""
        tasks.notify_student_session_timeslot_booking_freezes_tomorrow(
            self.timeslot_reg.id, self.app_reg.id
        )

        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.get()

        # Prepare safe string fields
        title = notification.title or ""
        email_body = notification.email_body or ""
        note = notification.note or ""
        heading = notification.heading or ""

        self.assertTrue(notification.email_sent)
        self.assertIn("Timeslot Booking", title)
        self.assertIn("Closes Tomorrow", title)

        # Check that disclaimer is included in the email
        self.assertIn(self.ss_reg.disclaimer or "", email_body)
        self.assertIn("important to remember the following disclaimer", email_body)

        # Check that the date/time is included in the email body (2025-10-11 is tomorrow)
        self.assertIn("2025-10-11 13:00", email_body)
        self.assertIn("finalize your timeslot or unbook", note)
        self.assertIn(self.company.name, heading)

        self.assertEqual(
            notification.button_link,
            f"{MOCK_APP_BASE_URL}/sessions/book/{self.company.id}",
        )

    # --- Registration Open Task Test (SS version) ---

    def test_notify_student_session_registration_open_regular(self) -> None:
        """Tests the broadcast for regular student session opening."""
        tasks.notify_student_session_registration_open(self.ss_reg.id)

        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.get()

        # Prepare safe string fields
        title = notification.title or ""
        body = notification.body or ""

        self.assertEqual(notification.notification_topic, "broadcast")
        self.assertIn("Registration Open:", title)
        self.assertIn("Student Session", title)
        self.assertIn("Student Session", body)
        self.assertIn(self.company.name, body)

    def test_notify_student_session_registration_open_company_event(self) -> None:
        """Tests the broadcast for company event registration opening."""
        tasks.notify_student_session_registration_open(self.ss_event.id)

        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.get()

        # Prepare safe string fields
        title = notification.title or ""
        body = notification.body or ""

        self.assertIn("Registration Open:", title)
        self.assertIn("Company Event", title)
        self.assertIn("Company Event", body)
        self.assertIn(self.company.name, body)
