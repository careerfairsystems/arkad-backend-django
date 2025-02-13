from datetime import datetime, timezone, timedelta

from django.contrib.auth.models import AbstractUser
import jwt

from arkad.settings import SECRET_KEY


class User(AbstractUser):
    def create_jwt_token(self) -> str:
        return jwt.encode({
            "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=5),
            "user_id": self.id,
        }, SECRET_KEY, algorithm="HS512")
