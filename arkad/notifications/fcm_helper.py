import logging
from datetime import datetime, timedelta
from pathlib import Path

import firebase_admin  # type: ignore[import-untyped]
from firebase_admin import credentials, messaging
from firebase_admin.messaging import Message  # type: ignore[import-untyped]

from arkad import settings
from arkad.settings import DEBUG


def log_notification(msg: Message) -> None:
    recipient = None
    if msg.token:
        recipient = msg.token
    elif msg.topic:
        recipient = f"topic {msg.topic}"

    if msg.notification and recipient is not None:
        logging.info(
            msg=f"Sent notification with title {msg.notification.title} and body {msg.notification.body} to {recipient} at {datetime.now()}"
        )


class FCMHelper:
    def __init__(self, cert_path: Path):
        if cert_path.exists() and not firebase_admin._apps:
            cred = credentials.Certificate(cert_path)
            firebase_admin.initialize_app(cred)
        elif not DEBUG:
            raise FileNotFoundError(f"Firebase cert not found at {cert_path}")

    @staticmethod
    def send_to_token(token: str, title: str, body: str) -> str:
        """
        Sends a notification to a specific device using its FCM token.
        See https://firebase.google.com/docs/cloud-messaging/js/client
        """
        msg = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=token,
        )
        response = messaging.send(msg)
        log_notification(msg)
        return str(response)

    @staticmethod
    def send_to_topic(topic: str, title: str, body: str) -> str:
        """
        Sends a notification to a topic.
        The topic must be created in the Firebase console and the user must be subscribed to the topic.
        See https://firebase.google.com/docs/cloud-messaging/js/topic-messaging
        """
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            topic=topic,
        )

        response = messaging.send(message)
        log_notification(message)
        return str(response)

    def send_event_reminder(
        self, user_id: int, event_id: int, title: str, body: str
    ) -> None:
        """
        Sends a notification to the user that they have an event coming up.
        The notification is only sent if the user has a ticket to the event.
        10 minutes is used to account for possible delays in task scheduling.
        """
        from user_models.models import User
        from event_booking.models import Event

        try:
            user = User.objects.get(id=user_id)
            if not user.fcm_token:
                return

            event = Event.objects.get(id=event_id)
            if event.verify_user_has_ticket(user_id):
                self.send_to_token(user.fcm_token, title, body)
        except (User.DoesNotExist, Event.DoesNotExist):
            pass

    def send_student_session_reminder(
        self, user_id: int, session_id: int, time_delta: timedelta, title: str, body: str
    ) -> None:
        """
        Sends a notification to the user that they have a student session coming up.
        The notification is only sent if the user has been accepted to the session and
        the current time is within 10 minutes of the notification time (session start time - time_delta).
        10 minutes is used to account for possible delays in task scheduling.
        """
        from user_models.models import User
        from student_sessions.models import (
            StudentSession,
            StudentSessionApplication,
            SessionType,
        )
        from django.utils import timezone

        try:
            user = User.objects.get(id=user_id)
            if not user.fcm_token:
                return

            session = StudentSession.objects.get(id=session_id)
            application = StudentSessionApplication.objects.get(
                user_id=user_id, student_session_id=session_id
            )

            if not application.is_accepted():
                return

            notification_time = None
            if session.session_type == SessionType.REGULAR:
                timeslot = session.timeslots.first()
                if timeslot:
                    notification_time = timeslot.start_time
            elif session.session_type == SessionType.COMPANY_EVENT:
                notification_time = session.company_event_at

            if not notification_time:
                return

            if abs(timezone.now() - (notification_time - time_delta)) > timedelta(
                minutes=10
            ):
                return

            self.send_to_token(user.fcm_token, title, body)

        except (
            User.DoesNotExist,
            StudentSession.DoesNotExist,
            StudentSessionApplication.DoesNotExist,
        ):
            pass

    def send_student_session_application_accepted(
        self, user_id: int, session_id: int
    ) -> None:
        """
        Sends a notification to the user that their application to the student session has been accepted.
        """
        from user_models.models import User
        from student_sessions.models import StudentSession, SessionType

        try:
            user = User.objects.get(id=user_id)
            if not user.fcm_token:
                return

            session = StudentSession.objects.get(id=session_id)

            if session.session_type == SessionType.REGULAR:
                title = f"Du har blivit antagen till en student session med {session.company.name}!"
                body = f"Grattis! Du har blivit antagen till en student session med {session.company.name}, kolla i appen för mer info."
                self.send_to_token(user.fcm_token, title, body)
            elif session.session_type == SessionType.COMPANY_EVENT:
                title = f"Du har blivit antagen till ett företagsevent med {session.company.name}!"
                body = f"Grattis! Du har blivit antagen till ett företagsevent med {session.company.name}, kolla i appen för mer info."
                self.send_to_token(user.fcm_token, title, body)
        except (User.DoesNotExist, StudentSession.DoesNotExist):
            pass


fcm = FCMHelper(settings.FIREBASE_CERT_PATH)
