import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, cast

import firebase_admin  # type: ignore[import-untyped]
from firebase_admin import credentials, messaging
from firebase_admin.messaging import Message  # type: ignore[import-untyped]

from arkad import settings
from arkad.settings import DEBUG, ENVIRONMENT
from user_models.models import User
from django.core.cache import cache


def log_notification(msg: Message) -> None:
    recipient = None
    if msg.token:
        token = msg.token
        masked = (token[:4] + "…" + token[-4:]) if len(token) >= 8 else "****"
        recipient = f"token {masked}"
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
    def send(
        title: str,
        body: str,
        token: Optional[str] = None,
        topic: Optional[str] = None,
        data: Optional[Dict[str, str]] = None,
        link: Optional[str] = None,
    ) -> bool:
        """
        Generic FCM send helper that supports:
        - token OR topic
        - optional data payload
        - optional link (opens page/app)
        """
        if ENVIRONMENT == "TESTING":
            return True

        if token and token.startswith("TEST_FCM_TOKEN"):
            return True

        if not token and not topic:
            logging.warning("No token or topic provided for FCM message")
            return False

        # Build notification block
        notification = messaging.Notification(
            title=title,
            body=body,
        )

        # Add link for Android Click Actions
        android_notification = None
        if link:
            android_notification = messaging.AndroidNotification(
                click_action="FLUTTER_NOTIFICATION_CLICK"
            )
            if data is None:
                data = {}
            data["link"] = link

        # Safeguard, if sending with topic check cache key last_topic_notification_{topic}
        # If it exists do not send and instead raise. This is to avoid spamming topics.
        # The cache has a 1-minute expiry so only one notification per minute per topic.

        # Include a hashed version of the title in the cache key to allow different notifications
        # to be sent to the same topic within the rate limit window.
        # Use a deterministic hash function for consistency across runs.
        hashed_title: str = hashlib.md5(title.encode()).hexdigest()

        # Determine cache key based on whether sending to topic or token
        target: str = (
            topic if topic else hashlib.md5(cast(str, token).encode()).hexdigest()
        )
        cache_key: str = f"last_topic_notification_{target}_{hashed_title}"
        if cache.get(cache_key):
            logging.exception(
                f"Skipping FCM notification to {target[:20]} due to rate limiting."
            )
            return False
        msg = messaging.Message(
            notification=notification,
            token=token,
            topic=topic,
            data=data,
            android=messaging.AndroidConfig(notification=android_notification)
            if android_notification
            else None,
        )
        cache.set(cache_key, True, timeout=60)  # 1 minute rate limit

        logging.info(messaging.send(msg))
        log_notification(msg)
        return True

    @classmethod
    def send_to_user(
        cls,
        user: User,
        title: str,
        body: str,
        data: dict | None = None,  # type: ignore[type-arg]
        link: str | None = None,
    ) -> bool:
        if not user.fcm_token:
            return False
        return cls.send(
            title=title,
            body=body,
            token=user.fcm_token,
            data=data,
            link=link,
        )

    @classmethod
    def send_to_topic(
        cls,
        topic: str,
        title: str,
        body: str,
        data: dict | None = None,  # type: ignore[type-arg]
        link: str | None = None,
    ) -> bool:
        production_mode: bool = not DEBUG and ENVIRONMENT == "production"
        topic = (
            "debug_" + topic
            if not production_mode and not topic.startswith("debug_")
            else topic
        )
        return cls.send(
            title=title,
            body=body,
            topic=topic,
            data=data,
            link=link,
        )


fcm = FCMHelper(settings.FIREBASE_CERT_PATH)
