import logging
from datetime import timedelta

import uuid
from celery import shared_task  # type: ignore[import-untyped]

from event_booking.models import Event, Ticket
from notifications.models import Notification
from student_sessions.models import StudentSession, SessionType, StudentSessionTimeslot
from user_models.models import User
from arkad.settings import APP_BASE_URL, make_local_time

logger = logging.getLogger(__name__)

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
    "companies": {
      "list": "/companies",
      "detail": "/companies/detail/{companyId}"
    },
"""


@shared_task  # type: ignore
def notify_event_tomorrow(ticket_uuid: uuid.UUID) -> None:
    # Notify the user that they have an event tomorrow
    ticket: Ticket = Ticket.objects.select_related("user", "event").get(
        uuid=ticket_uuid, used=False
    )
    user: User = ticket.user
    event: Event = ticket.event

    # Convert to local timezone for display
    local_start_time = make_local_time(event.start_time)
    location_string: str = (
        f"\nThe event will be held in {event.location}" if event.location else ""
    )
    Notification.objects.create(
        target_user=user,
        title=f"Reminder: {event.name} is tomorrow!",
        body=f"Don't forget the event at {event.location} tomorrow at {local_start_time.strftime('%H:%M')}!{location_string}",
        greeting=f"Hi {user.first_name},",
        heading=f"Reminder: {event.name} is tomorrow!",
        button_text="View Event",
        button_link=f"{APP_BASE_URL}/events/detail/{event.id}",
        note="We look forward to seeing you there!",
        email_sent=True,
        fcm_sent=True,
    )


@shared_task  # type: ignore
def notify_event_one_hour(ticket_uuid: uuid.UUID) -> None:
    # Notify the user that they have an event in one hour
    ticket: Ticket = Ticket.objects.select_related("user", "event").get(
        uuid=ticket_uuid, used=False
    )

    # Convert to local timezone for display
    local_start_time = make_local_time(ticket.event.start_time)

    Notification.objects.create(
        target_user=ticket.user,
        title=f"Reminder: {ticket.event.name} is in one hour!",
        body=f"Don't forget to come to {ticket.event.location} in one hour at {local_start_time.strftime('%H:%M')}!",
        fcm_sent=True,
    )


@shared_task  # type: ignore
def notify_student_session_tomorrow(
    user_id: int, student_session_id: int, timeslot_id: int
) -> None:
    # Notify the user that they have a student session tomorrow
    user = User.objects.get(id=user_id)
    session: StudentSession = StudentSession.objects.get(id=student_session_id)
    timeslot = StudentSessionTimeslot.objects.get(id=timeslot_id)
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

    # Add the start and end time of the timeslot to the body
    local_start_time = make_local_time(timeslot.start_time)
    local_end_time = make_local_time(timeslot.start_time + timedelta(timeslot.duration))
    body += f" Your timeslot is from {local_start_time.strftime('%H:%M')} to {local_end_time.strftime('%H:%M')}."
    if session.disclaimer:
        body += f" Remember the following disclaimer: {session.disclaimer}"

    Notification.objects.create(
        target_user=user,
        title=title,
        body=body,
        greeting=f"Hi {user.first_name},",
        heading=title,
        button_text="View Session",
        button_link=f"{APP_BASE_URL}/sessions/book/{session.company.id if session.company else ''}",
        note="We look forward to seeing you there!",
        email_sent=True,
        fcm_sent=True,
    )


@shared_task  # type: ignore
def notify_student_session_one_hour(
    user_id: int, student_session_id: int, timeslot_id: int
) -> None:
    # Notify the user that they have a student session in one hour
    user = User.objects.get(id=user_id)
    session: StudentSession = StudentSession.objects.get(id=student_session_id)
    timeslot = StudentSessionTimeslot.objects.get(id=timeslot_id)

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

    # Add the start and end time of the timeslot to the body
    local_start_time = make_local_time(timeslot.start_time)
    local_end_time = make_local_time(timeslot.start_time + timedelta(timeslot.duration))
    body += f" Your timeslot is from {local_start_time.strftime('%H:%M')} to {local_end_time.strftime('%H:%M')}."
    if session.disclaimer:
        body += f" Remember the following disclaimer: {session.disclaimer}"

    Notification.objects.create(
        target_user=user,
        title=title,
        body=body,
        fcm_sent=True,
    )


@shared_task  # type: ignore
def notify_event_registration_open(event_id: int) -> None:
    # Both for lunch lectures, company visits (events?), and Student sessions
    # Registration for lunch lecture with XXX has opened - Just a notification
    # Registration for company visit with XXX has opened - Just a notification
    # Send by topic
    event: Event = Event.objects.get(id=event_id)
    Notification.objects.create(
        notification_topic="broadcast",
        title=f"Registration for {event.name} has opened!",
        body=f"Reserve a spot for {event.name} now! Open the Arkad app to register.",
        fcm_sent=True,
    )


@shared_task  # type: ignore
def notify_student_session_registration_open(student_session_id: int) -> None:
    session: StudentSession = StudentSession.objects.get(id=student_session_id)
    title: str
    if session.session_type == SessionType.REGULAR:
        title = (
            f"Registration for student session with {session.company.name} has opened!"
        )
    elif session.session_type == SessionType.COMPANY_EVENT:
        title = (
            f"Registration for a company event with {session.company.name} has opened!"
        )
    else:
        title = f"Registration for an event with {session.company.name} has opened!"

    body = f"Reserve a spot for the session with {session.company.name} now! Open the Arkad app to register."

    Notification.objects.create(
        notification_topic="broadcast",
        title=title,
        body=body,
        fcm_sent=True,
    )


@shared_task  # type: ignore
def notify_event_registration_closes_tomorrow(event_id: int) -> None:
    """
    This should only be sent to users which are signed up for the event.
    It is to remind people to unbook if they can't attend.
    24 hours before booking freezes.
    """
    event = Event.objects.get(id=event_id)
    for user_ticket in event.tickets.prefetch_related("user").filter(used=False).all():
        Notification.objects.create(
            target_user=user_ticket.user,
            title=f"Reminder: Registration for {event.name} closes tomorrow!",
            body=f"Don't forget to unbook your spot for {event.name} if you can't attend!",
            greeting=f"Hi {user_ticket.user.first_name},",
            heading=f"Reminder: Registration for {event.name} closes tomorrow!",
            button_text="View Event",
            button_link=f"{APP_BASE_URL}/events/detail/{event.id}/ticket",
            note="We look forward to seeing you there!",
            email_sent=True,
            fcm_sent=True,
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

    # Convert to local timezone for display
    local_start_time = make_local_time(timeslot_obj.start_time)
    body: str = "Don't forget to unbook your spot if you can no longer attend."
    if ss.disclaimer:
        body += f" Remember the following disclaimer: {ss.disclaimer}"

    Notification.objects.create(
        target_user=application.user,
        title=f"Reminder: Booking for timeslot {local_start_time.strftime('%Y-%m-%d %H:%M')} closes tomorrow!",
        body=body,
        greeting=f"Hi {application.user.first_name},",
        heading=f"Reminder: Booking for timeslot {local_start_time.strftime('%Y-%m-%d %H:%M')} closes tomorrow!",
        button_text="View Session",
        button_link=f"{APP_BASE_URL}/sessions/book/{ss.company.id if ss.company else ''}",
        note="We look forward to seeing you there!",
        email_sent=True,
        fcm_sent=True,
    )
