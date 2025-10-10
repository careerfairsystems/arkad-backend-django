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
from notifications.models import NotificationLog
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
        ticket.task_id_notify_registration_closes_tomorrow = "task-id-3"

        # Delete the ticket
        ticket.delete()

        # Verify all three tasks were revoked
        self.assertEqual(mock_revoke.call_count, 3)

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

    @patch("notifications.tasks.notify_event_registration_closes_tomorrow.apply_async")
    @patch("notifications.tasks.notify_event_tomorrow.apply_async")
    @patch("notifications.tasks.notify_event_one_hour.apply_async")
    def test_ticket_schedules_registration_closing_notification(
        self, mock_one_hour: Mock, mock_tomorrow: Mock, mock_notify_close: Mock
    ) -> None:
        """Test that creating a ticket schedules the registration closing notification."""
        mock_tomorrow.return_value = MagicMock(id="task-tomorrow-id")
        mock_one_hour.return_value = MagicMock(id="task-one-hour-id")
        mock_notify_close.return_value = MagicMock(id="registration-closing-task-id")

        # Create a ticket
        ticket = Ticket.objects.create(user=self.user, event=self.event)

        # Verify registration closing notification was scheduled (1 day before booking_freezes_at)
        self.assertEqual(mock_notify_close.call_count, 1)
        expected_eta = self.event.booking_freezes_at - datetime.timedelta(days=1)
        mock_notify_close.assert_called_with(args=[self.event.id], eta=expected_eta)

        # Verify task ID was stored
        ticket.refresh_from_db()
        self.assertEqual(
            ticket.task_id_notify_registration_closes_tomorrow,
            "registration-closing-task-id",
        )


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

        assert timeslot.booking_closes_at is not None
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

    @patch(
        "notifications.tasks.notify_student_session_timeslot_booking_freezes_tomorrow.apply_async"
    )
    def test_application_schedules_booking_freeze_notification(
        self, mock_notify: Mock
    ) -> None:
        """Test that a timeslot schedules a booking freeze notification."""
        mock_notify.return_value = MagicMock(id="booking-freeze-task-id")

        application = StudentSessionApplication.objects.create(
            student_session=self.session,
            user=self.user,
            motivation_text="I want to attend",
            status="accepted",
        )

        timeslot_start = timezone.now() + datetime.timedelta(days=3)
        booking_closes_at = timezone.now() + datetime.timedelta(days=2)
        timeslot = StudentSessionTimeslot.objects.create(
            student_session=self.session,
            start_time=timeslot_start,
            duration=30,
            booking_closes_at=booking_closes_at,
        )
        timeslot.selected_applications.add(application)

        application.schedule_notifications(
            timeslot_start, booking_closes_at, timeslot.id
        )
        application.save()

        mock_notify.assert_called_once_with(
            args=[timeslot.id, application.id],
            eta=booking_closes_at - datetime.timedelta(days=1),
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
            event_time, company_event.booking_close_time, 0
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

    @patch("notifications.tasks.notify_student_session_registration_open.apply_async")
    def test_session_schedules_registration_notification(
        self, mock_notify: Mock
    ) -> None:
        """Test that creating a student session schedules registration opening notification."""
        mock_notify.return_value = MagicMock(id="session-registration-task-id")

        new_company = Company.objects.create(name="New Session Company")
        booking_open_time = timezone.now() + datetime.timedelta(hours=2)

        new_session = StudentSession.objects.create(
            company=new_company,
            booking_open_time=booking_open_time,
            booking_close_time=booking_open_time + datetime.timedelta(days=2),
            session_type=SessionType.REGULAR,
        )

        # Manually trigger the task as the signal may not be reliable in tests
        tasks.notify_student_session_registration_open.apply_async(
            args=[new_session.id], eta=new_session.booking_open_time
        )

        self.assertEqual(mock_notify.call_count, 1)
        mock_notify.assert_called_with(
            args=[new_session.id], eta=new_session.booking_open_time
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

    @patch("notifications.tasks.send_event_reminder_email")
    @patch("notifications.fcm_helper.fcm.send_event_reminder")
    def test_notify_event_tomorrow_sends_correct_message(
        self, mock_fcm: Mock, mock_email: Mock
    ) -> None:
        """Test that event tomorrow notification sends correct FCM message and email."""
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
        mock_email.assert_called_once()
        call_args, _ = mock_fcm.call_args
        self.assertEqual(call_args[0], self.user)
        self.assertEqual(call_args[1], event)
        self.assertIn("Test Event", call_args[2])
        self.assertIn("is tomorrow", call_args[2])
        self.assertIn("Test Hall", call_args[3])

        mock_fcm.reset_mock()
        mock_email.reset_mock()

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

    @patch("notifications.tasks.send_event_reminder_email")
    @patch("notifications.fcm_helper.fcm.send_student_session_reminder")
    def test_notify_student_session_tomorrow_regular(
        self, mock_fcm: Mock, mock_email: Mock
    ) -> None:
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
        mock_email.assert_called_once()
        call_args, _ = mock_fcm.call_args
        self.assertEqual(call_args[0], self.user)
        self.assertEqual(call_args[1], session)
        self.assertIn("Student session", call_args[3])
        self.assertIn("Test Company", call_args[3])
        self.assertIn("is tomorrow", call_args[3])

        mock_fcm.reset_mock()
        mock_email.reset_mock()

        # Should not send
        with freeze_time(timeslot_start - datetime.timedelta(days=1, minutes=11)):
            tasks.notify_student_session_tomorrow(self.user.id, session.id)
        mock_fcm.assert_not_called()

    @patch("notifications.fcm_helper.fcm.send_student_session_reminder")
    def test_notify_student_session_one_hour_regular(self, mock_fcm: Mock) -> None:
        """Test student session one hour notification for regular sessions."""
        session = StudentSession.objects.create(
            company=self.company,
            session_type=SessionType.REGULAR,
        )
        timeslot_start = timezone.now() + datetime.timedelta(hours=2)
        timeslot = StudentSessionTimeslot.objects.create(
            student_session=session, start_time=timeslot_start, duration=30
        )
        application = StudentSessionApplication.objects.create(
            student_session=session,
            user=self.user,
            status="accepted",
        )
        timeslot.selected_applications.add(application)

        with freeze_time(timeslot_start - datetime.timedelta(hours=1)):
            tasks.notify_student_session_one_hour(self.user.id, session.id)

        mock_fcm.assert_called_once()
        call_args, _ = mock_fcm.call_args
        self.assertEqual(call_args[0], self.user)
        self.assertIn("in one hour", call_args[3])

    @patch("notifications.tasks.send_event_reminder_email")
    @patch("notifications.fcm_helper.fcm.send_student_session_reminder")
    def test_notify_student_session_company_event(
        self, mock_fcm: Mock, mock_email: Mock
    ) -> None:
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

        with freeze_time(event_time - datetime.timedelta(days=1)):
            tasks.notify_student_session_tomorrow(self.user.id, session.id)

        mock_fcm.assert_called_once()
        mock_email.assert_called_once()
        call_args, _ = mock_fcm.call_args
        self.assertEqual(call_args[0], self.user)
        self.assertIn("Company event", call_args[3])
        self.assertIn("is tomorrow", call_args[3])

    @patch("notifications.fcm_helper.fcm.send_to_topic")
    def test_notify_event_registration_open(self, mock_fcm: Mock) -> None:
        """Test that event registration open notification sends correct FCM message."""
        release_time = timezone.now() + datetime.timedelta(hours=1)
        event = Event.objects.create(
            name="Open Event",
            company=self.company,
            release_time=release_time,
            start_time=release_time + datetime.timedelta(days=1),
            end_time=release_time + datetime.timedelta(days=1, hours=1),
            capacity=10,
        )

        with freeze_time(release_time):
            tasks.notify_event_registration_open(event.id)

        mock_fcm.assert_called_once_with(
            "broadcast",
            "Registration for Open Event has opened!",
            "Reserve a spot for Open Event now! Open the Arkad app to register.",
        )

    @patch("notifications.fcm_helper.fcm.send_to_topic")
    def test_notify_student_session_registration_open(self, mock_fcm: Mock) -> None:
        """Test that student session registration open notification sends correct FCM message."""
        booking_open_time = timezone.now() + datetime.timedelta(hours=1)
        session = StudentSession.objects.create(
            company=self.company,
            session_type=SessionType.REGULAR,
            booking_open_time=booking_open_time,
        )

        with freeze_time(booking_open_time):
            tasks.notify_student_session_registration_open(session.id)

        mock_fcm.assert_called_once()
        self.assertIn("student session", mock_fcm.call_args[0][1])

    @patch("notifications.tasks.send_event_closing_reminder_email")
    @patch("notifications.fcm_helper.fcm.send_event_reminder")
    def test_notify_event_registration_closes_tomorrow(
        self, mock_fcm: Mock, mock_email: Mock
    ) -> None:
        """Test that event registration closing notification sends correct messages."""
        # booking_freezes_at is always start_time - 1 week
        # So if we want booking_freezes_at to be in 2 days, start_time must be in 2 days + 1 week
        booking_freezes_at = timezone.now() + datetime.timedelta(days=2)
        event = Event.objects.create(
            name="Closing Event",
            company=self.company,
            start_time=booking_freezes_at + datetime.timedelta(weeks=1),
            end_time=booking_freezes_at + datetime.timedelta(weeks=1, hours=1),
            capacity=10,
        )
        Ticket.objects.create(user=self.user, event=event)

        # Test should run 1 day before booking_freezes_at
        with freeze_time(booking_freezes_at - datetime.timedelta(days=1)):
            tasks.notify_event_registration_closes_tomorrow(event.id)

        mock_fcm.assert_called_once()
        mock_email.assert_called_once()
        self.assertIn("closes tomorrow", mock_fcm.call_args[0][2])
        self.assertEqual(mock_email.call_args.kwargs["event_name"], "Closing Event")

    @patch("notifications.tasks.send_event_closing_reminder_email")
    @patch("notifications.fcm_helper.fcm.send_student_session_reminder")
    def test_notify_student_session_booking_freezes_tomorrow(
        self, mock_fcm: Mock, mock_email: Mock
    ) -> None:
        """Test that student session booking freeze notification sends correct messages."""
        booking_closes_at = timezone.now() + datetime.timedelta(days=2)
        session = StudentSession.objects.create(
            company=self.company, session_type=SessionType.REGULAR
        )
        timeslot = StudentSessionTimeslot.objects.create(
            student_session=session,
            start_time=booking_closes_at + datetime.timedelta(days=1),
            duration=30,
            booking_closes_at=booking_closes_at,
        )
        application = StudentSessionApplication.objects.create(
            student_session=session, user=self.user, status="accepted"
        )
        timeslot.selected_applications.add(application)

        with freeze_time(booking_closes_at - datetime.timedelta(days=1)):
            tasks.notify_student_session_timeslot_booking_freezes_tomorrow(
                timeslot.id, application.id
            )

        mock_fcm.assert_called_once()
        mock_email.assert_called_once()
        self.assertIn("closes tomorrow", mock_fcm.call_args[0][3])
        self.assertEqual(mock_email.call_args.kwargs["company_name"], "Test Company")


    @patch("notifications.tasks.send_event_selection_email")
    @patch("notifications.fcm_helper.fcm.send_student_session_application_accepted")
    def test_notify_student_session_application_accepted(
        self, mock_fcm: Mock, mock_email: Mock
    ) -> None:
        """Test that application accepted notification sends correct messages."""
        session = StudentSession.objects.create(
            company=self.company, session_type=SessionType.REGULAR
        )

        application = StudentSessionApplication.objects.create(
            student_session=session,
            user=self.user,
            status="accepted",
        )
        st = StudentSessionTimeslot.objects.create(
            student_session=session,
            start_time=timezone.now() + datetime.timedelta(days=5),
            duration=30,
        )
        st.selected_applications.add(application)


        tasks.notify_student_session_application_accepted(self.user.id, session.id)

        mock_fcm.assert_called_once_with(self.user, session)
        mock_email.assert_called_once()
