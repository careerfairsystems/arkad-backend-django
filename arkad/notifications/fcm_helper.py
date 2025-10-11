import logging
from datetime import datetime, timedelta
from pathlib import Path

import firebase_admin  # type: ignore[import-untyped]
from firebase_admin import credentials, messaging
from firebase_admin.messaging import Message  # type: ignore[import-untyped]

from arkad import settings
from arkad.settings import DEBUG, ENVIRONMENT
from event_booking.models import Event
from student_sessions.models import (
    StudentSession,
    StudentSessionApplication,
    SessionType,
)
from user_models.models import User


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


def send_student_session_reminder(
    user: User,
    session: StudentSession,
    time_delta: timedelta,
    title: str,
    body: str,
) -> None:
    """
    Sends a notification to the user that they have a student session coming up.
    The notification is only sent if the user has been accepted to the session and
    the current time is within 10 minutes of the notification time (session start time - time_delta).
    10 minutes is used to account for possible delays in task scheduling.
    """

    if not user.fcm_token:
        return

    application = StudentSessionApplication.objects.filter(
        user_id=user.id, student_session_id=session.id
    ).first()

    if not application or not application.is_accepted():
        return

    FCMHelper.send_to_user(user, title, body)


def send_student_session_application_accepted(
    user: User, session: StudentSession
) -> None:
    """
    Sends a notification to the user that their application to the student session has been accepted.
    """
    if not user.fcm_token:
        return

    if session.session_type == SessionType.REGULAR:
        title = (
            f"You have been accepted to a student session with {session.company.name}!"
        )
        body = f"Congratulations! You have been accepted to a student session with {session.company.name}, check the app for more info."
        FCMHelper.send_to_user(user, title, body)
    elif session.session_type == SessionType.COMPANY_EVENT:
        title = (
            f"You have been accepted to a company event with {session.company.name}!"
        )
        body = f"Congratulations! You have been accepted to a company event with {session.company.name}, check the app for more info."
        FCMHelper.send_to_user(user, title, body)


def send_event_reminder(user: User, event: Event, title: str, body: str) -> None:
    """
    Sends a notification to the user that they have an event coming up.
    The notification is only sent if the user has a ticket to the event.
    10 minutes is used to account for possible delays in task scheduling.
    """
    if not user.fcm_token:
        return

    if event.verify_user_has_ticket(user.id):
        FCMHelper.send_to_user(user, title, body)


class FCMHelper:
    def __init__(self, cert_path: Path):
        if cert_path.exists() and not firebase_admin._apps:
            cred = credentials.Certificate(cert_path)
            firebase_admin.initialize_app(cred)
        elif not DEBUG:
            raise FileNotFoundError(f"Firebase cert not found at {cert_path}")

    @staticmethod
    def send_to_user(user: User, title: str, body: str) -> bool:
        """
        Sends a notification to a specific user using its FCM token.
        See https://firebase.google.com/docs/cloud-messaging/js/client
        """
        if not user.fcm_token:
            return False
        msg = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=user.fcm_token,
        )
        logging.info(messaging.send(msg))
        log_notification(msg)
        return True

    @staticmethod
    def send_to_topic(topic: str, title: str, body: str) -> bool:
        """
        Sends a notification to a topic.
        The topic must be created in the Firebase console and the user must be subscribed to the topic.
        See https://firebase.google.com/docs/cloud-messaging/js/topic-messaging
        """

        send_topic_message_condition: bool = not DEBUG and ENVIRONMENT == "production"
        if (
            send_topic_message_condition
        ):  # Avoid sending messages to topics in debug mode
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                topic=topic,
            )

            logging.info(messaging.send(message))
            log_notification(message)
        return send_topic_message_condition


fcm = FCMHelper(settings.FIREBASE_CERT_PATH)
