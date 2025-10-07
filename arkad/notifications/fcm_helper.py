import logging
from datetime import datetime
from pathlib import Path

import firebase_admin  # type: ignore[import-untyped]
from firebase_admin import credentials, messaging
from firebase_admin.messaging import Message  # type: ignore[import-untyped]

from arkad import settings


class NotificationLog:
    def log(self, msg: Message) -> None:
        recipient = None
        if msg.token:
            recipient = msg.token
        elif msg.topic:
            recipient = f"topic {msg.topic}"

        if msg.notification and recipient is not None:
            logging.info(msg=f"Sent notification with title {msg.notification.title} and body {msg.notification.body} to {recipient} at {datetime.now()}")

logger = NotificationLog()

class FCMHelper:
    
    def __init__(self, cert_path: Path):
        if cert_path.exists() and not firebase_admin._apps:
            cred = credentials.Certificate(cert_path)
            firebase_admin.initialize_app(cred)
    
    def send_to_token(self, token: str, title: str, body: str) -> str:
        msg = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=token,
        )
        response = messaging.send(msg)
        logger.log(msg)
        return str(response)
    
    def send_to_topic(self, topic: str, title: str, body: str) -> str:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            topic=topic,
        )
        
        response = messaging.send(message)
        logger.log(message)
        return str(response)

fcm = FCMHelper(settings.FIREBASE_CERT_PATH)
