from pathlib import Path

import firebase_admin
from firebase_admin import credentials, messaging

from arkad import settings
from notifications.fcm_helper import FCMHelper


class FCMHelper:
    
    def __init__(self, cert_path: Path):
        if not firebase_admin._apps:
            cred = credentials.Certificate(cert_path)
            firebase_admin.initialize_app(cred)
    
    def send_to_token(self, token: str, title: str, body: str):
        msg = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=token,
        )
        pass
    
fcm = FCMHelper(settings.BASE_DIR / "private/firebaseCert.json")
