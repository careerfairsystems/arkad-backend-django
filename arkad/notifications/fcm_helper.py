import logging
from datetime import datetime
from pathlib import Path

import firebase_admin  # type: ignore[import-untyped]
from firebase_admin import credentials, messaging
from firebase_admin.messaging import Message  # type: ignore[import-untyped]

from arkad import settings
from arkad.settings import DEBUG, ENVIRONMENT
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


class FCMHelper:
    def __init__(self, cert_path: Path):
        if cert_path.exists() and not firebase_admin._apps:
            cred = credentials.Certificate(cert_path)
            firebase_admin.initialize_app(cred)
        elif not DEBUG and ENVIRONMENT == "production":
            raise FileNotFoundError(f"Firebase cert not found at {cert_path}")

    @staticmethod
    def send_to_user(user: User, title: str, body: str) -> bool:
        """
        Sends a notification to a specific user using its FCM token.
        See https://firebase.google.com/docs/cloud-messaging/js/client
        """
        if not user.fcm_token:
            return False
        if user.fcm_token.startswith("TEST_FCM_TOKEN"):
            # Mock for testing
            return True
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

        production_mode: bool = not DEBUG and ENVIRONMENT == "production"
        topic = (
            "debug_" + topic
            if not production_mode and not topic.startswith("debug_")
            else topic
        )
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            topic=topic,
        )

        logging.info(messaging.send(message))
        log_notification(message)
        return True


fcm = FCMHelper(settings.FIREBASE_CERT_PATH)
