"""
Tests for notification scheduling without actually sending tasks.
Uses mocking to verify that tasks are scheduled correctly.
"""

import datetime
from unittest.mock import patch, MagicMock, Mock
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from companies.models import Company
from event_booking.models import Event, Ticket
from notifications import tasks
from student_sessions.models import (
    StudentSession,
    StudentSessionApplication,
    StudentSessionTimeslot,
    SessionType,
)
from user_models.models import User


class EventNotificationSchedulingTests(TestCase):
    """Test event notification scheduling without sending actual tasks."""

    def setUp(self) -> None:
        self.company = Company.objects.create(name="Test Company")
        self.user = User.objects.create_user(
            username="testuser",
            password="password",
            first_name="Test",
            last_name="User",
            email="test@example.com",
        )

        # Create event that starts in 2 days
        self.event_start = timezone.now() + datetime.timedelta(days=2)
        self.event = Event.objects.create(
            name="Test Event",
            description="Test Description",
            type="lu",
            location="Test Location",
            company=self.company,
            release_time=timezone.now() - datetime.timedelta(days=1),
            start_time=self.event_start,
            end_time=self.event_start + datetime.timedelta(hours=2),
            visible_time=timezone.now() - datetime.timedelta(days=2),
            capacity=100,
        )

    @patch("notifications.tasks.notify_event_tomorrow.apply_async")
    @patch("notifications.tasks.notify_event_one_hour.apply_async")
    def test_ticket_schedules_notifications(
        self, mock_one_hour: Mock, mock_tomorrow: Mock
    ) -> None:
        """Test that creating a ticket schedules both notification tasks."""
        # Setup mock return values
        mock_tomorrow.return_value = MagicMock(id="task-tomorrow-id")
        mock_one_hour.return_value = MagicMock(id="task-one-hour-id")

        # Create a ticket
        ticket = Ticket.objects.create(user=self.user, event=self.event)

        # Manually call schedule_notifications since save() checks if pk exists
        # ticket.schedule_notifications(self.event.start_time)
        # ticket.save()

        # Verify tomorrow notification was scheduled
        self.assertEqual(mock_tomorrow.call_count, 1)
        mock_tomorrow.assert_called_with(
            args=[self.user.id, self.event.id],
            eta=self.event.start_time - datetime.timedelta(hours=24),
        )

        # Verify one hour notification was scheduled
        self.assertEqual(mock_one_hour.call_count, 1)
        mock_one_hour.assert_called_with(
            args=[self.user.id, self.event.id],
            eta=self.event.start_time - datetime.timedelta(hours=1),
        )

        # Verify task IDs were stored
        ticket.refresh_from_db()
        self.assertEqual(ticket.task_id_notify_event_tomorrow, "task-tomorrow-id")
        self.assertEqual(ticket.task_id_notify_event_in_one_hour, "task-one-hour-id")

    @patch("celery.result.AsyncResult.revoke")
    def test_ticket_removes_notifications_on_delete(self, mock_revoke: Mock) -> None:
        """Test that deleting a ticket revokes scheduled tasks."""
        ticket = Ticket.objects.create(user=self.user, event=self.event)
        ticket.task_id_notify_event_tomorrow = "task-id-1"
        ticket.task_id_notify_event_in_one_hour = "task-id-2"

        # Delete the ticket
        ticket.delete()

        # Verify both tasks were revoked
        self.assertEqual(mock_revoke.call_count, 2)

    @patch("notifications.tasks.notify_event_registration_open.apply_async")
    def test_event_schedules_registration_notification(self, mock_notify: Mock) -> None:
        """Test that creating an event schedules registration opening notification."""
        mock_notify.return_value = MagicMock(id="registration-task-id")

        # Create a new company for this event to avoid conflicts
        new_company = Company.objects.create(name="New Company")

        new_event = Event.objects.create(
            name="New Event",
            description="Test",
            type="lu",
            location="Location",
            company=new_company,
            release_time=timezone.now() + datetime.timedelta(hours=1),
            start_time=timezone.now() + datetime.timedelta(days=7),
            end_time=timezone.now() + datetime.timedelta(days=7, hours=2),
            visible_time=timezone.now(),
            capacity=50,
        )

        # Verify registration opening notification was scheduled
        self.assertEqual(mock_notify.call_count, 1)
        mock_notify.assert_called_with(args=[new_event.id], eta=new_event.release_time)


class StudentSessionNotificationSchedulingTests(TestCase):
    """Test student session notification scheduling without sending actual tasks."""

    def setUp(self) -> None:
        self.company = Company.objects.create(name="Test Company")
        self.user = User.objects.create_user(
            username="testuser",
            password="password",
            first_name="Test",
            last_name="User",
            email="test@example.com",
            is_student=True,
        )

        # Create a regular student session
        self.session = StudentSession.objects.create(
            company=self.company,
            booking_open_time=timezone.now() - datetime.timedelta(days=1),
            booking_close_time=timezone.now() + datetime.timedelta(days=7),
            session_type=SessionType.REGULAR,
        )

    @patch("notifications.tasks.notify_student_session_tomorrow.apply_async")
    @patch("notifications.tasks.notify_student_session_one_hour.apply_async")
    def test_application_schedules_notifications(
        self, mock_one_hour: Mock, mock_tomorrow: Mock
    ) -> None:
        """Test that accepting an application and selecting a timeslot schedules notifications."""
        # Setup mocks
        mock_tomorrow.return_value = MagicMock(id="session-task-tomorrow-id")
        mock_one_hour.return_value = MagicMock(id="session-task-one-hour-id")

        # Create application
        application = StudentSessionApplication.objects.create(
            student_session=self.session,
            user=self.user,
            motivation_text="I want to attend",
        )

        # Accept the application
        application.status = "accepted"
        application.save()

        # Create a timeslot
        timeslot_start = timezone.now() + datetime.timedelta(days=3)
        timeslot = StudentSessionTimeslot.objects.create(
            student_session=self.session,
            start_time=timeslot_start,
            duration=30,
        )

        # Add the application to the timeslot
        timeslot.selected_applications.add(application)

        # Manually trigger notification scheduling
        application.schedule_notifications(
            timeslot_start, timeslot.booking_closes_at, timeslot.id
        )
        application.save()

        # Verify notifications were scheduled
        mock_tomorrow.assert_called_once_with(
            args=[self.user.id, self.session.id],
            eta=timeslot_start - datetime.timedelta(hours=24),
        )

        mock_one_hour.assert_called_once_with(
            args=[self.user.id, self.session.id],
            eta=timeslot_start - datetime.timedelta(hours=1),
        )

        # Verify task IDs were stored
        application.refresh_from_db()
        self.assertEqual(
            application.task_id_notify_timeslot_tomorrow, "session-task-tomorrow-id"
        )
        self.assertEqual(
            application.task_id_notify_timeslot_in_one_hour, "session-task-one-hour-id"
        )

    @patch("celery.result.AsyncResult.revoke")
    def test_application_removes_notifications(self, mock_revoke: Mock) -> None:
        """Test that removing notifications properly revokes tasks."""
        application = StudentSessionApplication.objects.create(
            student_session=self.session,
            user=self.user,
            status="accepted",
        )

        application.task_id_notify_timeslot_tomorrow = "task-id-1"
        application.task_id_notify_timeslot_in_one_hour = "task-id-2"

        # Remove notifications
        application.remove_notifications()

        # Verify tasks were revoked
        self.assertEqual(mock_revoke.call_count, 2)

    @patch("notifications.tasks.notify_student_session_tomorrow.apply_async")
    @patch("notifications.tasks.notify_student_session_one_hour.apply_async")
    def test_company_event_schedules_notifications(
        self, mock_one_hour: Mock, mock_tomorrow: Mock
    ) -> None:
        """Test that company events schedule notifications correctly."""
        # Setup mocks
        mock_tomorrow.return_value = MagicMock(id="company-event-tomorrow")
        mock_one_hour.return_value = MagicMock(id="company-event-one-hour")

        # Create a new company for the company event to avoid OneToOne constraint
        event_company = Company.objects.create(name="Event Company")

        # Create a company event session
        event_time = timezone.now() + datetime.timedelta(days=5)
        company_event = StudentSession.objects.create(
            company=event_company,
            booking_open_time=timezone.now() - datetime.timedelta(days=1),
            booking_close_time=timezone.now() + datetime.timedelta(days=4),
            session_type=SessionType.COMPANY_EVENT,
            company_event_at=event_time,
        )

        # Create and accept application
        application = StudentSessionApplication.objects.create(
            student_session=company_event,
            user=self.user,
            motivation_text="Interested in company event",
            status="accepted",
        )

        # Schedule notifications
        application.schedule_notifications(
            event_time, company_event.booking_close_time, None
        )
        application.save()

        # Verify notifications were scheduled with correct timing
        mock_tomorrow.assert_called_once_with(
            args=[self.user.id, company_event.id],
            eta=event_time - datetime.timedelta(hours=24),
        )

        mock_one_hour.assert_called_once_with(
            args=[self.user.id, company_event.id],
            eta=event_time - datetime.timedelta(hours=1),
        )
        application.refresh_from_db()
        self.assertEqual(
            application.task_id_notify_timeslot_tomorrow, "company-event-tomorrow"
        )
        self.assertEqual(
            application.task_id_notify_timeslot_in_one_hour, "company-event-one-hour"
        )


class NotificationTaskTests(TestCase):
    """Test the actual notification task logic (with mocked FCM)."""

    def setUp(self) -> None:
        self.company = Company.objects.create(name="Test Company")
        self.user = User.objects.create_user(
            username="testuser",
            password="password",
            first_name="Test",
            last_name="User",
            email="test@example.com",
            fcm_token="test-fcm-token",
        )

    @patch("notifications.fcm_helper.fcm.send_event_reminder")
    def test_notify_event_tomorrow_sends_correct_message(self, mock_fcm: Mock) -> None:
        """Test that event tomorrow notification sends correct FCM message."""
        event_start = timezone.now() + datetime.timedelta(days=2)
        event = Event.objects.create(
            name="Test Event",
            description="Test",
            type="lu",
            location="Test Hall",
            company=self.company,
            start_time=event_start,
            end_time=event_start + datetime.timedelta(hours=2),
            capacity=100,
        )
        Ticket.objects.create(user=self.user, event=event)

        # Should send
        with freeze_time(event_start - datetime.timedelta(days=1)):
            tasks.notify_event_tomorrow(self.user.id, event.id)
        mock_fcm.assert_called_once()
        call_args, _ = mock_fcm.call_args
        self.assertEqual(call_args[0], self.user)
        self.assertEqual(call_args[1], event)
        self.assertIn("Test Event", call_args[2])
        self.assertIn("is tomorrow", call_args[2])
        self.assertIn("Test Hall", call_args[3])

        mock_fcm.reset_mock()

        # Should not send
        with freeze_time(event_start - datetime.timedelta(days=1, minutes=11)):
            tasks.notify_event_tomorrow(self.user.id, event.id)
        mock_fcm.assert_not_called()

    @patch("notifications.fcm_helper.fcm.send_event_reminder")
    def test_notify_event_one_hour_sends_correct_message(self, mock_fcm: Mock) -> None:
        """Test that event one hour notification sends correct FCM message."""
        event_start = timezone.now() + datetime.timedelta(hours=2)
        event = Event.objects.create(
            name="Test Event",
            description="Test",
            type="lu",
            location="Test Hall",
            company=self.company,
            start_time=event_start,
            capacity=100,
            end_time=event_start + datetime.timedelta(hours=2),
        )
        Ticket.objects.create(user=self.user, event=event)

        # Should send
        with freeze_time(event_start - datetime.timedelta(hours=1)):
            tasks.notify_event_one_hour(self.user.id, event.id)
        mock_fcm.assert_called_once()
        call_args, _ = mock_fcm.call_args
        self.assertEqual(call_args[0], self.user)
        self.assertEqual(call_args[1], event)
        self.assertIn("in one hour", call_args[2])

        mock_fcm.reset_mock()

        # Should not send
        with freeze_time(event_start - datetime.timedelta(hours=1, minutes=11)):
            tasks.notify_event_one_hour(self.user.id, event.id)
        mock_fcm.assert_not_called()

    @patch("notifications.fcm_helper.fcm.send_student_session_reminder")
    def test_notify_student_session_tomorrow_regular(self, mock_fcm: Mock) -> None:
        """Test student session tomorrow notification for regular sessions."""

        session = StudentSession.objects.create(
            company=self.company,
            session_type=SessionType.REGULAR,
        )
        timeslot_start = timezone.now() + datetime.timedelta(days=2)
        timeslot = StudentSessionTimeslot.objects.create(
            student_session=session, start_time=timeslot_start, duration=30
        )
        application = StudentSessionApplication.objects.create(
            student_session=session,
            user=self.user,
            status="accepted",
        )
        timeslot.selected_applications.add(application)

        # Should send
        with freeze_time(timeslot_start - datetime.timedelta(days=1)):
            tasks.notify_student_session_tomorrow(self.user.id, session.id)
        mock_fcm.assert_called_once()
        call_args, _ = mock_fcm.call_args
        self.assertEqual(call_args[0], self.user)
        self.assertIn("Student session", call_args[3])
        self.assertIn("Test Company", call_args[3])
        self.assertIn("is tomorrow", call_args[3])

        mock_fcm.reset_mock()

        # Should not send
        with freeze_time(timeslot_start - datetime.timedelta(days=1, minutes=11)):
            tasks.notify_student_session_tomorrow(self.user.id, session.id)
        mock_fcm.assert_not_called()

    @patch("notifications.fcm_helper.fcm.send_student_session_reminder")
    def test_notify_student_session_company_event(self, mock_fcm: Mock) -> None:
        """Test student session notification for company events."""

        event_time = timezone.now() + datetime.timedelta(days=2)
        session = StudentSession.objects.create(
            company=self.company,
            session_type=SessionType.COMPANY_EVENT,
            company_event_at=event_time,
        )
        StudentSessionApplication.objects.create(
            student_session=session,
            user=self.user,
            status="accepted",
        )

        # Should send
        with freeze_time(event_time - datetime.timedelta(days=1)):
            tasks.notify_student_session_tomorrow(self.user.id, session.id)
        mock_fcm.assert_called_once()
        call_args, _ = mock_fcm.call_args
        self.assertIn("Company event", call_args[3])
        self.assertIn("Test Company", call_args[3])

        mock_fcm.reset_mock()

        # Should not send
        with freeze_time(event_time - datetime.timedelta(days=1, minutes=11)):
            tasks.notify_student_session_tomorrow(self.user.id, session.id)
        mock_fcm.assert_not_called()

    @patch("notifications.fcm_helper.fcm.send_to_token")
    def test_notify_student_session_skips_pending_application(
        self, mock_fcm: Mock
    ) -> None:
        """Test that notifications are not sent for pending applications."""
        from notifications.tasks import notify_student_session_tomorrow

        session = StudentSession.objects.create(
            company=self.company,
            booking_open_time=timezone.now() - datetime.timedelta(days=1),
            booking_close_time=timezone.now() + datetime.timedelta(days=7),
            session_type=SessionType.REGULAR,
        )

        # Create pending application
        StudentSessionApplication.objects.create(
            student_session=session,
            user=self.user,
            status="pending",
        )

        # Call the task
        notify_student_session_tomorrow(self.user.id, session.id)

        # Verify FCM was NOT called for pending applications
        mock_fcm.assert_not_called()

    @patch("notifications.fcm_helper.fcm.send_to_topic")
    def test_notify_event_registration_open(self, mock_fcm_topic: Mock) -> None:
        """Test event registration opening notification."""

        release_time = timezone.now() + datetime.timedelta(hours=1)
        event = Event.objects.create(
            name="Test Event",
            description="Test",
            type="lu",
            location="Test Hall",
            company=self.company,
            release_time=release_time,
            start_time=release_time + datetime.timedelta(days=1),
            end_time=release_time + datetime.timedelta(days=1, hours=2),
            capacity=10,
        )

        # Should send
        with freeze_time(release_time):
            tasks.notify_event_registration_open(event.id)
        mock_fcm_topic.assert_called_once()
        call_args, _ = mock_fcm_topic.call_args
        self.assertEqual(call_args[0], "broadcast")
        self.assertIn("Test Event", call_args[1])
        self.assertIn("has opened", call_args[1])

        mock_fcm_topic.reset_mock()

        # Should not send
        with freeze_time(release_time - datetime.timedelta(minutes=11)):
            tasks.notify_event_registration_open(event.id)
        mock_fcm_topic.assert_not_called()

    @patch("notifications.fcm_helper.fcm.send_to_topic")
    def test_notify_student_session_registration_open(
        self, mock_fcm_topic: Mock
    ) -> None:
        """Test student session registration opening notification."""

        booking_open_time = timezone.now() + datetime.timedelta(hours=1)
        session = StudentSession.objects.create(
            company=self.company,
            session_type=SessionType.REGULAR,
            booking_open_time=booking_open_time,
        )

        # Should send
        with freeze_time(booking_open_time):
            tasks.notify_student_session_registration_open(session.id)
        mock_fcm_topic.assert_called_once()
        call_args, _ = mock_fcm_topic.call_args
        self.assertEqual(call_args[0], "broadcast")
        self.assertIn("student session", call_args[1])
        self.assertIn("Test Company", call_args[1])

        mock_fcm_topic.reset_mock()

        # Should not send
        with freeze_time(booking_open_time - datetime.timedelta(minutes=11)):
            tasks.notify_student_session_registration_open(session.id)
        mock_fcm_topic.assert_not_called()
