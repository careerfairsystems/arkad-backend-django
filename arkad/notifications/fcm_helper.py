from pathlib import Path

import firebase_admin
from firebase_admin import credentials, messaging

from arkad import settings


class FCMHelper:
    
    def __init__(self, cert_path: Path):
        if not firebase_admin._apps:
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
        return response
    
    def send_to_topic(self, topic: str, title: str, body: str) -> str:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            topic=topic,
        )
        
        response = messaging.send(message)
        return response

    
fcm = FCMHelper(settings.BASE_DIR / "private/firebaseCert.json")
