from datetime import timedelta

from django.utils import timezone
from celery import shared_task  # type: ignore[import-untyped]

from event_booking.models import Event
from notifications.fcm_helper import fcm
from student_sessions.models import StudentSession, SessionType, StudentSessionTimeslot
from user_models.models import User
from email_app.emails import (
    send_event_reminder_email,
    send_event_closing_reminder_email,
    send_event_selection_email,
)
from notifications.models import NotificationLog
from arkad.settings import APP_BASE_URL

"""
The routes to the app are:

    "events": {
      "list": "/events",
      "detail": "/events/detail/{eventId}",
      "ticket": "/events/detail/{eventId}/ticket"
    },
    "student_sessions": {
      "list": "/sessions",
      "apply": "/sessions/apply/{companyId}",
      "book": "/sessions/book/{companyId}"
    },
"""


@shared_task  # type: ignore
def notify_event_tomorrow(user_id: int, event_id: int) -> None:
    # Notify the user that they have an event tomorrow
    user = User.objects.get(id=user_id)
    event: Event = Event.objects.get(id=event_id)
    if abs(timezone.now() - (event.start_time - timedelta(days=1))) > timedelta(
        minutes=10
    ):
        return

    fcm.send_event_reminder(
        user,
        event,
        f"Reminder: {event.name} is tomorrow!",
        f"Don't forget the event at {event.location} tomorrow at {event.start_time.strftime('%H:%M')}!",
    )
    send_event_reminder_email(
        email=user.email,
        event_name=event.name or "",
        company_name=event.company.name if event.company else "",
        event_type=event.get_event_type_display(),
        event_start=event.start_time,
        event_description=event.description or "",
        location=event.location,
        button_link=f"{APP_BASE_URL}/events/detail/{event.id}",
        hours_before=24,
    )


@shared_task  # type: ignore
def notify_event_one_hour(user_id: int, event_id: int) -> None:
    # Notify the user that they have an event in one hour
    user = User.objects.get(id=user_id)
    event: Event = Event.objects.get(id=event_id)
    if abs(timezone.now() - (event.start_time - timedelta(hours=1))) > timedelta(
        minutes=10
    ):
        return

    fcm.send_event_reminder(
        user,
        event,
        f"Reminder: {event.name} is in one hour!",
        f"Don't forget to come to {event.location} in one hour at {event.start_time.strftime('%H:%M')}!",
    )


@shared_task  # type: ignore
def notify_student_session_tomorrow(user_id: int, student_session_id: int) -> None:
    # Notify the user that they have a student session tomorrow
    user = User.objects.get(id=user_id)
    session: StudentSession = StudentSession.objects.get(id=student_session_id)

    notification_time = None
    if session.session_type == SessionType.REGULAR:
        timeslot = session.timeslots.first()
        if timeslot:
            notification_time = timeslot.start_time
    elif session.session_type == SessionType.COMPANY_EVENT:
        notification_time = session.company_event_at

    if not notification_time:
        return

    if abs(timezone.now() - (notification_time - timedelta(days=1))) > timedelta(
        minutes=10
    ):
        return

    title = ""
    body = ""
    if session.session_type == SessionType.REGULAR:
        title = f"Reminder: Student session with {session.company.name} is tomorrow!"
        body = (
            f"Don't forget your student session with {session.company.name} tomorrow!"
        )
    elif session.session_type == SessionType.COMPANY_EVENT:
        title = f"Reminder: Company event with {session.company.name} is tomorrow!"
        body = f"Don't forget your company event with {session.company.name} tomorrow!"

    fcm.send_student_session_reminder(user, session, timedelta(days=1), title, body)
    if notification_time:
        send_event_reminder_email(
            email=user.email,
            event_name=session.name or "",
            company_name=session.company.name if session.company else "",
            event_type="Student Session"
            if session.session_type == SessionType.REGULAR
            else "Company Event",
            event_start=notification_time,
            event_description=session.description or "",
            button_link=f"{APP_BASE_URL}/sessions/book/{session.company.id if session.company else ''}",
            hours_before=24,
        )


@shared_task  # type: ignore
def notify_student_session_one_hour(user_id: int, student_session_id: int) -> None:
    # Notify the user that they have a student session in one hour
    user = User.objects.get(id=user_id)
    session: StudentSession = StudentSession.objects.get(id=student_session_id)

    notification_time = None
    if session.session_type == SessionType.REGULAR:
        timeslot = session.timeslots.first()
        if timeslot:
            notification_time = timeslot.start_time
    elif session.session_type == SessionType.COMPANY_EVENT:
        notification_time = session.company_event_at

    if not notification_time:
        return

    if abs(timezone.now() - (notification_time - timedelta(hours=1))) > timedelta(
        minutes=10
    ):
        return

    title = ""
    body = ""
    if session.session_type == SessionType.REGULAR:
        title = f"Reminder: Student session with {session.company.name} is in one hour!"
        body = f"Don't forget your student session with {session.company.name} in one hour!"
    elif session.session_type == SessionType.COMPANY_EVENT:
        title = f"Reminder: Company event with {session.company.name} is in one hour!"
        body = (
            f"Don't forget your company event with {session.company.name} in one hour!"
        )

    fcm.send_student_session_reminder(user, session, timedelta(hours=1), title, body)


@shared_task  # type: ignore
def notify_event_registration_open(event_id: int) -> None:
    # Both for lunch lectures, company visits (events?), and Student sessions
    # Registration for lunch lecture with XXX has opened - Just a notification
    # Registration for company visit with XXX has opened - Just a notification
    # Send by topic
    event: Event = Event.objects.get(id=event_id)
    if event.release_time and abs(timezone.now() - event.release_time) > timedelta(
        minutes=10
    ):
        return
    fcm.send_to_topic(
        "broadcast",
        f"Registration for {event.name} has opened!",
        f"Reserve a spot for {event.name} now! Open the Arkad app to register.",
    )


@shared_task  # type: ignore
def notify_student_session_registration_open(student_session_id: int) -> None:
    session: StudentSession = StudentSession.objects.get(id=student_session_id)
    if not session.booking_open_time or abs(
        timezone.now() - session.booking_open_time
    ) > timedelta(minutes=10):
        return
    if session.session_type == SessionType.REGULAR:
        fcm.send_to_topic(
            "broadcast",
            f"Registration for student session with {session.company.name} has opened!",
            f"Reserve a spot for the student session with {session.company.name} now! Open the Arkad app to register.",
        )
    elif session.session_type == SessionType.COMPANY_EVENT:
        fcm.send_to_topic(
            "broadcast",
            f"Registration for company event with {session.company.name} has opened!",
            f"Reserve a spot for the company event with {session.company.name} now! Open the Arkad app to register.",
        )


@shared_task  # type: ignore
def notify_event_registration_closes_tomorrow(event_id: int) -> None:
    """
    This should only be sent to users which are signed up for the event.
    It is to remind people to unbook if they can't attend.
    24 hours before booking freezes.
    """
    event = Event.objects.get(id=event_id)
    if event.booking_freezes_at and abs(
        timezone.now() - (event.booking_freezes_at - timedelta(days=1))
    ) > timedelta(minutes=10):
        return
    for user_ticket in event.tickets.prefetch_related("user").filter(used=False).all():
        fcm.send_event_reminder(
            user_ticket.user,
            event,
            f"Reminder: Registration for {event.name} closes tomorrow!",
            f"Don't forget to unbook your spot for {event.name} if you can't attend!",
        )
        if event.booking_freezes_at:
            send_event_closing_reminder_email(
                email=user_ticket.user.email,
                event_name=event.name or "",
                company_name=event.company.name if event.company else "",
                event_type=event.get_event_type_display(),
                closes_at=event.booking_freezes_at,
                event_description=event.description or "",
                location=event.location,
                button_link=f"{APP_BASE_URL}/events/detail/{event.id}/ticket",
            )


@shared_task  # type: ignore
def notify_student_session_timeslot_booking_freezes_tomorrow(
    timeslot_id: int, application_id: int
) -> None:
    """
    This should only be sent to user which have been accepted to the session.
    It is to remind people to book their timeslot if they haven't already.
    24 hours before booking freezes.
    """
    from student_sessions.models import StudentSessionTimeslot

    timeslot_obj = StudentSessionTimeslot.objects.get(id=timeslot_id)
    application = timeslot_obj.selected_applications.get(id=application_id)
    ss = timeslot_obj.student_session

    # Verify accepted and timing
    if (
        not application.is_accepted()
        or not timeslot_obj.booking_closes_at
        or abs(timezone.now() - (timeslot_obj.booking_closes_at - timedelta(days=1)))
        > timedelta(minutes=10)
    ):
        return
    fcm.send_student_session_reminder(
        application.user,
        timeslot_obj.student_session,
        timedelta(days=1),
        f"Reminder: Booking for timeslot {timeslot_obj.start_time.strftime('%Y-%m-%d %H:%M')} closes tomorrow!",
        "Don't forget to unbook your spot if you can no longer attend."
        + " Remember the following disclaimer: "
        + (ss.disclaimer or "")
        if ss.disclaimer
        else "",
    )
    if timeslot_obj.booking_closes_at:
        send_event_closing_reminder_email(
            email=application.user.email,
            event_name=ss.name or "",
            company_name=ss.company.name if ss.company else "",
            event_type="Student Session",
            closes_at=timeslot_obj.booking_closes_at,
            event_description=ss.description or "",
            button_link=f"{APP_BASE_URL}/sessions/book/{ss.company.id if ss.company else ''}",
            disclaimer=ss.disclaimer,
        )


@shared_task  # type: ignore
def notify_student_session_application_accepted(
    user_id: int, student_session_id: int
) -> None:
    # Notify that a user has gotten their application accepted
    # Not a scheduled notification - this is triggered
    user = User.objects.get(id=user_id)
    session = StudentSession.objects.get(id=student_session_id)
    application = session.studentsessionapplication_set.filter(user_id=user_id, status="accepted").first()
    if not application:
        print("No accepted application found")
        return

    fcm.send_student_session_application_accepted(user, session)
    event_start_time = None
    if session.session_type == SessionType.COMPANY_EVENT:
        event_start_time = session.company_event_at

    send_event_selection_email(
        email=user.email,
        event_name=session.name or "",
        company_name=session.company.name if session.company else "",
        event_type="Student Session"
        if session.session_type == SessionType.REGULAR
        else "Company Event",
        event_start=event_start_time,
        event_description=session.description or "",
        button_link=f"{APP_BASE_URL}/sessions/book/{session.company.id if session.company else ''}",
        disclaimer=session.disclaimer,
    )
