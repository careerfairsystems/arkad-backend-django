from datetime import timedelta

from django.utils import timezone
from celery import shared_task  # type: ignore[import-untyped]

from event_booking.models import Event
from notifications.fcm_helper import fcm
from student_sessions.models import (
    StudentSession,
    SessionType
)
from user_models.models import User


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
        f"Påminnelse: {event.name} är imorgon!",
        f"Glöm inte eventet i {event.location} imorgon klockan {event.start_time.strftime('%H:%M')}!",
    )
    # TODO: Send email


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
        f"Påminnelse: {event.name} är om en timme!",
        f"Glöm inte att komma till {event.location} om en timme klockan {event.start_time.strftime('%H:%M')}!",
    )


@shared_task  # type: ignore
def notify_student_session_tomorrow(user_id: int, student_session_id: int) -> None:
    # Notify the user that they have a student session tomorrow
    user = User.objects.get(id=user_id)
    session: StudentSession = StudentSession.objects.get(id=student_session_id)
    title = ""
    body = ""
    if session.session_type == SessionType.REGULAR:
        title = f"Påminnelse: Student session med {session.company.name} är imorgon!"
        body = f"Glöm inte din student session med {session.company.name} imorgon!"
    elif session.session_type == SessionType.COMPANY_EVENT:
        title = f"Påminnelse: Företagsevent med {session.company.name} är imorgon!"
        body = f"Glöm inte ditt företagsevent med {session.company.name} imorgon!"

    fcm.send_student_session_reminder(user, session, timedelta(days=1), title, body)
    # TODO: Send email


@shared_task  # type: ignore
def notify_student_session_one_hour(user_id: int, student_session_id: int) -> None:
    # Notify the user that they have a student session in one hour
    user = User.objects.get(id=user_id)
    session: StudentSession = StudentSession.objects.get(id=student_session_id)
    title = ""
    body = ""
    if session.session_type == SessionType.REGULAR:
        title = (
            f"Påminnelse: Student session med {session.company.name} är om en timme!"
        )
        body = f"Glöm inte din student session med {session.company.name} om en timme!"
    elif session.session_type == SessionType.COMPANY_EVENT:
        title = f"Påminnelse: Företagsevent med {session.company.name} är om en timme!"
        body = f"Glöm inte ditt företagsevent med {session.company.name} om en timme!"

    fcm.send_student_session_reminder(user, session, timedelta(hours=1), title, body)


@shared_task  # type: ignore
def notify_event_registration_open(event_id: int) -> None:
    # Both for lunch lectures, company visits (events?), and Student sessions
    # Anmälan för lunchföreläsning med XXX har öppnat -Bara notis
    # Anmälan för företagsbesök med XXX har öppnat - Bara notis
    # Send by topic
    event: Event = Event.objects.get(id=event_id)
    if event.release_time and abs(timezone.now() - event.release_time) > timedelta(
        minutes=10
    ):
        return
    fcm.send_to_topic(
        "broadcast",
        f"Anmälan för {event.name} har öppnat!",
        f"Reservera en plats till {event.name} nu! Öppna Arkadappen för att anmäla dig.",
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
            f"Anmälan för student session med {session.company.name} har öppnat!",
            f"Reservera en plats till student session med {session.company.name} nu! Öppna Arkadappen för att anmäla dig.",
        )
    elif session.session_type == SessionType.COMPANY_EVENT:
        fcm.send_to_topic(
            "broadcast",
            f"Anmälan för företagsevent med {session.company.name} har öppnat!",
            f"Reservera en plats till företagsevent med {session.company.name} nu! Öppna Arkadappen för att anmäla dig.",
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
    for user in event.tickets.prefetch_related("user").filter(used=False).all():
        fcm.send_event_reminder(
            user.user,
            event,
            f"Påminnelse: Anmälan för {event.name} stänger imorgon!",
            f"Glöm inte att avboka din plats till {event.name} om du inte kan komma!",
        )
        # TODO: Send email

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
    if not application.is_accepted() or abs(
        timezone.now()
        - (timeslot_obj.booking_closes_at - timedelta(days=1))
    ) > timedelta(minutes=10):
        return
    fcm.send_student_session_reminder(
        application.user,
        timeslot_obj.student_session,
        timedelta(days=1),
        f"Påminnelse: Bokning för timeslot {timeslot_obj.start_time.strftime('%Y-%m-%d %H:%M')} stänger imorgon!",
        f"Glöm inte att avboka din plats om du inte längre kan komma." + " Remember the following disclaimer: " + ss.booking_disclaimer if ss.booking_disclaimer else "",
    )
    # TODO: Send email


@shared_task  # type: ignore
def notify_student_session_application_accepted(
    user_id: int, student_session_id: int
) -> None:
    # Notify that a user has gotten their application accepted
    # Not a scheduled notification - this is triggered
    user = User.objects.get(id=user_id)
    session = StudentSession.objects.get(id=student_session_id)
    fcm.send_student_session_application_accepted(user, session)
    # TODO: Send email
