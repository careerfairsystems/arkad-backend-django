from typing import Callable

import jwt
from django.http import HttpRequest
from ninja.security import HttpBearer

from arkad.jwt_utils import jwt_decode
from user_models.models import User


class AuthBearer(HttpBearer):
    def authenticate(self, request: HttpRequest, token: str) -> User:
        # Implement authentication
        decoded: dict[str, str] = jwt_decode(token)
        if "user_id" not in decoded:
            raise jwt.InvalidTokenError("No user id")
        try:
            user: User = User.objects.get(id=decoded["user_id"])
            if not user.is_active:
                raise jwt.InvalidTokenError("User is inactive")
        except User.DoesNotExist:
            raise jwt.InvalidTokenError("No such user")
        request.user = user
        return user


def anonymous(request: HttpRequest) -> str:
    return "<anonymous user>"


OPTIONAL_AUTH: list[AuthBearer | Callable[[HttpRequest], str]] = [
    AuthBearer(),
    anonymous,
]
