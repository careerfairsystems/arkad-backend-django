from datetime import timedelta

from django.utils import timezone
from celery import shared_task  # type: ignore[import-untyped]

from event_booking.models import Event
from notifications.fcm_helper import fcm
from student_sessions.models import (
    StudentSession,
    SessionType,
    StudentSessionApplication,
)
from user_models.models import User


@shared_task  # type: ignore
def notify_event_tomorrow(user_id: int, event_id: int) -> None:
    # Notify the user that they have an event tomorrow
    event: Event = Event.objects.get(id=event_id)
    if abs(timezone.now() - (event.start_time - timedelta(days=1))) > timedelta(
        minutes=10
    ):
        return

    token: str = User.objects.get(id=user_id).fcm_token
    if event.verify_user_has_ticket(user_id):
        fcm.send_to_token(
            token,
            f"Påminnelse: {event.name} är imorgon!",
            f"Glöm inte att komma till {event.location} imorgon klockan {event.start_time.strftime('%H:%M')}!",
        )


@shared_task  # type: ignore
def notify_event_one_hour(user_id: int, event_id: int) -> None:
    # Notify the user that they have an event in one hour
    event: Event = Event.objects.get(id=event_id)
    if abs(timezone.now() - (event.start_time - timedelta(hours=1))) > timedelta(
        minutes=10
    ):
        return

    token: str = User.objects.get(id=user_id).fcm_token
    if event.verify_user_has_ticket(user_id):
        fcm.send_to_token(
            token,
            f"Påminnelse: {event.name} är om en timme!",
            f"Glöm inte att komma till {event.location} om en timme klockan {event.start_time.strftime('%H:%M')}!",
        )


@shared_task  # type: ignore
def notify_student_session_tomorrow(user_id: int, student_session_id: int) -> None:
    # Notify the user that they have a student session tomorrow
    user: User = User.objects.get(id=user_id)
    token: str = user.fcm_token
    session: StudentSession = StudentSession.objects.get(id=student_session_id)

    # Verify user has an accepted application
    try:
        application = StudentSessionApplication.objects.get(
            user_id=user_id, student_session_id=student_session_id
        )
        if application.is_accepted():
            if session.session_type == SessionType.REGULAR:
                timeslot = application.student_session.timeslots.first()
                if not timeslot:
                    return
                if abs(
                    timezone.now() - (timeslot.start_time - timedelta(days=1))
                ) > timedelta(minutes=10):
                    return

                fcm.send_to_token(
                    token,
                    f"Påminnelse: Student session med {session.company.name} är imorgon!",
                    f"Glöm inte din student session med {session.company.name} imorgon!",
                )
            elif session.session_type == SessionType.COMPANY_EVENT:
                if abs(
                    timezone.now() - (session.company_event_at - timedelta(days=1))
                ) > timedelta(minutes=10):
                    return

                fcm.send_to_token(
                    token,
                    f"Påminnelse: Företagsevent med {session.company.name} är imorgon!",
                    f"Glöm inte ditt företagsevent med {session.company.name} imorgon!",
                )
    except StudentSessionApplication.DoesNotExist:
        pass


@shared_task  # type: ignore
def notify_student_session_one_hour(user_id: int, student_session_id: int) -> None:
    # Notify the user that they have a student session in one hour
    user: User = User.objects.get(id=user_id)
    token: str = user.fcm_token
    session: StudentSession = StudentSession.objects.get(id=student_session_id)

    # Verify user has an accepted application
    try:
        application = StudentSessionApplication.objects.get(
            user_id=user_id, student_session_id=student_session_id
        )
        if application.is_accepted():
            if session.session_type == SessionType.REGULAR:
                timeslot = application.student_session.timeslots.first()
                if not timeslot:
                    return
                if abs(
                    timezone.now() - (timeslot.start_time - timedelta(hours=1))
                ) > timedelta(minutes=10):
                    return

                fcm.send_to_token(
                    token,
                    f"Påminnelse: Student session med {session.company.name} är om en timme!",
                    f"Glöm inte din student session med {session.company.name} om en timme!",
                )
            elif session.session_type == SessionType.COMPANY_EVENT:
                if abs(
                    timezone.now() - (session.company_event_at - timedelta(hours=1))
                ) > timedelta(minutes=10):
                    return

                fcm.send_to_token(
                    token,
                    f"Påminnelse: Företagsevent med {session.company.name} är om en timme!",
                    f"Glöm inte ditt företagsevent med {session.company.name} om en timme!",
                )
    except StudentSessionApplication.DoesNotExist:
        pass


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
    # THIS IS FOR STUDENT SESSIONS: Defence companies (SAAB and FMV, any more?), append "swedish citizenship required"
    event = Event.objects.get(id=event_id)
    if event.end_time and abs(
        timezone.now() - (event.end_time - timedelta(days=1))
    ) > timedelta(minutes=10):
        return
    fcm.send_to_topic(
        "broadcast",
        f"Anmälan för {event.name} stänger imorgon!",
        f"Skynda att anmäla dig till {event.name}! Öppna Arkadappen för att anmäla dig.)",
    )


@shared_task  # type: ignore
def notify_student_session_application_accepted(
    user_id: int, student_session_id: int
) -> None:
    # Notify that a user has gotten their application accepted
    # Not a scheduled notification - this is triggered
    session: StudentSession = StudentSession.objects.get(id=student_session_id)
    user: User = User.objects.get(id=user_id)

    if session.session_type == SessionType.REGULAR:
        fcm.send_to_token(
            user.fcm_token,
            f"Du har blivit antagen till en student session med {session.company.name}!",
            f"Grattis! Du har blivit antagen till en student session med {session.company.name}, kolla i appen för mer info.",
        )
    elif session.session_type == SessionType.COMPANY_EVENT:
        fcm.send_to_token(
            user.fcm_token,
            f"Du har blivit antagen till ett företagsevent med {session.company.name}!",
            f"Grattis! Du har blivit antagen till ett företagsevent med {session.company.name}, kolla i appen för mer info.",
        )
