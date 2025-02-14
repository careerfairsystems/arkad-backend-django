from datetime import datetime, timezone, timedelta

from django.contrib.auth.models import AbstractUser
import jwt
from django.db import models
from arkad.settings import SECRET_KEY

class Company(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(null=True, blank=True)

class User(AbstractUser):
    is_company = models.BooleanField(default=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, default=None, null=True)

    def create_jwt_token(self) -> str:
        return "Bearer " + jwt.encode({
            "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=120),
            "user_id": self.id,
        }, SECRET_KEY, algorithm="HS512")
