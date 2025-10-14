import logging
import uuid
from celery import shared_task  # type: ignore[import-untyped]

from event_booking.models import Event, Ticket
from notifications.models import Notification
from student_sessions.models import StudentSession, SessionType, StudentSessionTimeslot
from user_models.models import User
from arkad.settings import APP_BASE_URL, make_local_time
from student_sessions.models import StudentSessionApplication

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


# --- Event Reminders ---


@shared_task  # type: ignore
def notify_event_tomorrow(ticket_uuid: uuid.UUID) -> None:
    """Notify the user that they have an event tomorrow (with email)."""
    try:
        # Select user and event to minimize queries
        ticket: Ticket = Ticket.objects.select_related("user", "event").get(
            uuid=ticket_uuid, used=False
        )
    except Ticket.DoesNotExist:
        logger.warning(f"Ticket with uuid {ticket_uuid} not found or already used.")
        return

    user: User = ticket.user
    event: Event = ticket.event

    # Convert to local timezone for display
    local_start_time = make_local_time(event.start_time).strftime("%H:%M")

    # Construct location string clearly
    location_str: str = f" at {event.location}" if event.location else ""

    # 1. FCM/Notification Body (Concise)
    title = f"Reminder: {event.name} is Tomorrow! 📅"
    fcm_body = f"Your event, {event.name}, starts tomorrow at {local_start_time}{location_str}. Don't miss out!"

    # 2. Email Body (Rich/Detailed)
    email_body = (
        f"You have a confirmed ticket for the event {event.name} starting tomorrow at {local_start_time}."
        f"{f' It will be held at {event.location}.' if event.location else ''}"
        f"\n\nPlease arrive on time to ensure you get your spot! If your plans have changed, we kindly ask you to unbook your ticket."
    )
    email_note = "We look forward to seeing you there!"

    link = f"{APP_BASE_URL}/events/detail/{event.id}"
    Notification.objects.create(
        target_user=user,
        title=title,
        body=fcm_body,  # Used for FCM
        email_body=email_body,  # Used for Email
        # Email fields
        greeting=f"Hi {user.first_name},",
        heading=f"Upcoming Event: {event.name}",
        button_text="View Your Ticket",
        button_link=link,
        fcm_link=link,
        note=email_note,
        email_sent=True,
        fcm_sent=True,
    )


@shared_task  # type: ignore
def notify_event_one_hour(ticket_uuid: uuid.UUID) -> None:
    """Notify the user that they have an event in one hour (FCM only)."""
    try:
        ticket: Ticket = Ticket.objects.select_related("user", "event").get(
            uuid=ticket_uuid, used=False
        )
    except Ticket.DoesNotExist:
        logger.warning(f"Ticket with uuid {ticket_uuid} not found or already used.")
        return

    event: Event = ticket.event

    # Convert to local timezone for display
    local_start_time = make_local_time(event.start_time).strftime("%H:%M")

    location_str: str = f" at {event.location}" if event.location else ""

    Notification.objects.create(
        target_user=ticket.user,
        title=f"Heads Up: {event.name} is in 1 Hour! ⏰",
        body=f"Your event starts in one hour{location_str} at {local_start_time}! Get ready.",
        fcm_sent=True,
        fcm_link=f"{APP_BASE_URL}/events/detail/{event.id}",
    )


# --- Student Session Reminders ---


def _get_session_notification_texts(
    session: StudentSession, timeslot: StudentSessionTimeslot, reminder_type: str
) -> tuple[str, str, str, str, str, str]:
    """Helper to generate consistent notification strings."""
    session_type_name = (
        "Company Event"
        if session.session_type == SessionType.COMPANY_EVENT
        else "Student Session"
    )
    company_name = session.company.name if session.company else "a company"

    # Calculate local times
    local_start_time = make_local_time(timeslot.start_time).strftime("%H:%M")

    time_info = f"Your timeslot begins at {local_start_time}."

    # Base titles and bodies
    if reminder_type == "tomorrow":
        title = f"Reminder: Your {session_type_name} with {company_name} is Tomorrow!"
        fcm_body = f"Don't forget your {session_type_name} with {company_name} tomorrow! {time_info}"

        email_heading = f"Your {session_type_name} Tomorrow"
        email_note = "We look forward to seeing you!"

    elif reminder_type == "one_hour":
        title = f"1 Hour Notice: {session_type_name} with {company_name} 🔔"
        fcm_body = f"Your {session_type_name} with {company_name} starts in one hour! {time_info}"
        email_heading = ""  # Not used for FCM-only
        email_note = ""  # Not used for FCM-only
    else:
        raise ValueError("Invalid reminder_type")

    # Add disclaimer if present (used in both FCM and Email body)
    disclaimer_str = ""
    if session.disclaimer:
        disclaimer_str = f" Remember the following disclaimer: {session.disclaimer}"

    return title, fcm_body, email_heading, email_note, time_info, disclaimer_str


@shared_task  # type: ignore
def notify_student_session_tomorrow(
    user_id: int, student_session_id: int, timeslot_id: int
) -> None:
    """Notify the user about a student session tomorrow (with email)."""
    try:
        user = User.objects.get(id=user_id)
        session: StudentSession = StudentSession.objects.select_related("company").get(
            id=student_session_id
        )
        timeslot = StudentSessionTimeslot.objects.get(id=timeslot_id)
    except (
        User.DoesNotExist,
        StudentSession.DoesNotExist,
        StudentSessionTimeslot.DoesNotExist,
    ):
        logger.warning(
            f"Could not find user {user_id}, session {student_session_id}, or timeslot {timeslot_id}."
        )
        return

    title, fcm_body_base, email_heading, email_note, time_info, disclaimer_str = (
        _get_session_notification_texts(session, timeslot, "tomorrow")
    )

    # 1. FCM/Notification Body (Concise)
    fcm_body = fcm_body_base + disclaimer_str

    # 2. Email Body (Rich/Detailed)
    email_body = (
        f"You have a confirmed timeslot for a {email_heading.replace('Your ', '').split(' Tomorrow')[0]} with {session.company.name} tomorrow. "
        f"{time_info} "
        f"\n\nPlease make sure to be on time for your session. "
        f"{disclaimer_str.replace(' Remember the following disclaimer:', ' It is important to remember the following disclaimer:')}"
    )
    link = (
        f"{APP_BASE_URL}/sessions/book/{session.company.id if session.company else ''}"
    )

    Notification.objects.create(
        target_user=user,
        title=title,
        body=fcm_body,  # Used for FCM
        email_body=email_body,  # Used for Email
        # Email fields
        greeting=f"Hi {user.first_name},",
        heading=email_heading,
        button_text="View Your Session",
        button_link=link,
        fcm_link=link,
        note=email_note,
        email_sent=True,
        fcm_sent=True,
    )


@shared_task  # type: ignore
def notify_student_session_one_hour(
    user_id: int, student_session_id: int, timeslot_id: int
) -> None:
    """Notify the user about a student session in one hour (FCM only)."""
    try:
        user = User.objects.get(id=user_id)
        session: StudentSession = StudentSession.objects.select_related("company").get(
            id=student_session_id
        )
        timeslot = StudentSessionTimeslot.objects.get(id=timeslot_id)
    except (
        User.DoesNotExist,
        StudentSession.DoesNotExist,
        StudentSessionTimeslot.DoesNotExist,
    ):
        logger.warning(
            f"Could not find user {user_id}, session {student_session_id}, or timeslot {timeslot_id}."
        )
        return

    title, fcm_body_base, _, _, _, disclaimer_str = _get_session_notification_texts(
        session, timeslot, "one_hour"
    )

    # 1. FCM/Notification Body (Concise)
    fcm_body = fcm_body_base + disclaimer_str

    Notification.objects.create(
        target_user=user,
        title=title,
        body=fcm_body,  # Used for FCM
        fcm_sent=True,
        fcm_link=f"{APP_BASE_URL}/sessions/book/{session.company.id if session.company else ''}",
    )


# --- Registration Open Notifications (Broadcast) ---


@shared_task  # type: ignore
def notify_event_registration_open(event_id: int) -> None:
    """Broadcast notification that registration for a general event has opened (FCM only)."""
    try:
        event: Event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        logger.warning(f"Event with id {event_id} not found.")
        return

    Notification.objects.create(
        notification_topic="broadcast",
        title=f"Registration Open: {event.name}! 🎉",
        body=f"Registration for {event.name} is now open! Reserve your spot right away.",
        fcm_sent=True,
        fcm_link=f"{APP_BASE_URL}/events/detail/{event.id}",
    )


@shared_task  # type: ignore
def notify_student_session_registration_open(student_session_id: int) -> None:
    """Broadcast notification that registration for a student session/company event has opened (FCM only)."""
    try:
        session: StudentSession = StudentSession.objects.select_related("company").get(
            id=student_session_id
        )
    except StudentSession.DoesNotExist:
        logger.warning(f"Student Session with id {student_session_id} not found.")
        return

    company_name = session.company.name if session.company else "an exciting company"

    if session.session_type == SessionType.REGULAR:
        event_type = "Student Session"
    elif session.session_type == SessionType.COMPANY_EVENT:
        event_type = "Company Event"
    else:
        event_type = "Event"

    title = f"Registration Open: {event_type} with {company_name}! 🤩"
    body = f"Registration for the {event_type} with {company_name} is now open! Apply or register via the app."

    Notification.objects.create(
        notification_topic="broadcast",
        title=title,
        body=body,
        fcm_sent=True,
        fcm_link=f"{APP_BASE_URL}/sessions/book/{session.company.id if session.company else ''}",
    )


# --- Registration Closing Reminders (with email) ---


@shared_task  # type: ignore
def notify_event_registration_closes_tomorrow(event_id: int) -> None:
    """
    Remind registered users that event registration/unbooking closes tomorrow (with email).
    """
    try:
        event = Event.objects.prefetch_related("tickets__user").get(id=event_id)
    except Event.DoesNotExist:
        logger.warning(f"Event with id {event_id} not found.")
        return

    # Filter for active tickets
    active_tickets = event.tickets.filter(used=False).select_related("user").all()

    for user_ticket in active_tickets:
        user = user_ticket.user
        title = f"Unbooking for {event.name} Closes Tomorrow! ⚠️"

        # 1. FCM/Notification Body (Concise)
        fcm_body = f"Registration/unbooking for {event.name} closes tomorrow! Please unbook your spot now if you can no longer attend."

        # 2. Email Body (Rich/Detailed)
        email_body = (
            f"The registration and unbooking window for {event.name} closes tomorrow. "
            f"If you are unable to attend, please unbook your ticket immediately. This is crucial to allow students on the waiting list to get a spot! "
            f"Thank you for being considerate."
        )

        link = f"{APP_BASE_URL}/events/detail/{event.id}/ticket"
        Notification.objects.create(
            target_user=user,
            title=title,
            body=fcm_body,  # Used for FCM
            email_body=email_body,  # Used for Email
            # Email fields
            greeting=f"Hi {user.first_name},",
            heading=f"Reminder: {event.name}",
            button_text="Manage Your Ticket",
            button_link=link,
            fcm_link=link,
            note="Thank you for helping us make the most of every spot!",
            email_sent=True,
            fcm_sent=True,
        )


@shared_task  # type: ignore
def notify_student_session_timeslot_booking_freezes_tomorrow(
    timeslot_id: int, application_id: int
) -> None:
    """
    Remind selected users that timeslot booking/unbooking closes tomorrow (with email).
    """
    try:
        # Import inside the task to avoid potential Celery startup issues/circular imports

        timeslot_obj = StudentSessionTimeslot.objects.select_related(
            "student_session__company"
        ).get(id=timeslot_id)
        # Note: Assuming this task is run for a user selected for this timeslot.
        application = StudentSessionApplication.objects.select_related("user").get(
            id=application_id
        )
    except (
        StudentSessionTimeslot.DoesNotExist,
        StudentSessionApplication.DoesNotExist,
    ):
        logger.warning(
            f"Timeslot {timeslot_id} or Application {application_id} not found."
        )
        return

    ss = timeslot_obj.student_session
    user = application.user
    company_name = ss.company.name if ss.company else "a company"
    session_type_name = (
        "Company Event"
        if ss.session_type == SessionType.COMPANY_EVENT
        else "Student Session"
    )

    # Convert to local timezone for display
    local_start_time = make_local_time(timeslot_obj.start_time).strftime(
        "%Y-%m-%d %H:%M"
    )

    disclaimer_info = (
        f" Remember the following disclaimer: {ss.disclaimer}" if ss.disclaimer else ""
    )

    title = f"Timeslot Booking for {session_type_name} Closes Tomorrow! ⏳"

    # 1. FCM/Notification Body (Concise)
    fcm_body: str = f"Booking for your confirmed timeslot ({local_start_time}) with {company_name} closes tomorrow. Finalize your booking or unbook your timeslot if you can no longer go! {disclaimer_info}"

    # 2. Email Body (Rich/Detailed)
    email_body: str = (
        f"The deadline for booking (and unbooking) your timeslot for the {session_type_name} with {company_name} is tomorrow. "
        f"Your specific timeslot starts at {local_start_time}."
        f"\n\nPlease take action now: Ensure you have confirmed your booking or unbook your spot if you can no longer attend. "
        f"{f'It is important to remember the following disclaimer: {ss.disclaimer}' if ss.disclaimer else ''}"
    )
    link = f"{APP_BASE_URL}/sessions/book/{ss.company.id if ss.company else ''}"
    Notification.objects.create(
        target_user=user,
        title=title,
        body=fcm_body,  # Used for FCM
        email_body=email_body,  # Used for Email
        # Email fields
        greeting=f"Hi {user.first_name},",
        heading=f"Timeslot Booking Closing: {session_type_name} with {company_name}",
        button_text="View & Book Timeslot",
        button_link=link,
        fcm_link=link,
        note="Please finalize your timeslot or unbook your entire session if needed. Thank you!",
        email_sent=True,
        fcm_sent=True,
    )
