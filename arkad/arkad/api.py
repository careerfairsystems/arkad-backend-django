from typing import Union, Any, List, Optional, override

from django.http import HttpRequest, HttpResponse
from ninja import NinjaAPI, Swagger
from ninja.constants import NOT_SET, NOT_SET_TYPE
from ninja.security import HttpBearer
import jwt
from ninja.throttling import BaseThrottle

from arkad.customized_django_ninja import Router
from arkad.jwt_utils import jwt_decode, PUBLIC_KEY, PublicKeySchema
from user_models.models import User, AuthenticatedRequest
from user_models.api import router as user_router
from student_sessions.api import router as student_sessions_router
from companies.api import router as company_router
from event_booking.api import router as event_booking_router


class AuthBearer(HttpBearer):
    def authenticate(self, request: HttpRequest, token: str) -> User:
        # Implement authentication
        decoded: dict[str, str] = jwt_decode(token)
        if "user_id" not in decoded:
            raise jwt.InvalidTokenError("No user id")
        try:
            user: User = User.objects.get(id=decoded["user_id"])
        except User.DoesNotExist:
            raise jwt.InvalidTokenError("No such user")
        request.user = user
        return user


class CustomNinjaAPI(NinjaAPI):
    @override
    def add_router(
        self,
        prefix: str,
        router: Union[Router, str],
        *,
        auth: Any = NOT_SET,
        throttle: Union[BaseThrottle, List[BaseThrottle], NOT_SET_TYPE] = NOT_SET,
        tags: Optional[List[str]] = None,
        parent_router: Optional[Router] = None,
    ) -> None:
        """
        Adds a router to the API with the specified prefix.

        This will complain if using the incorrect Router, you should use arkad.Router instead of ninja.Router.
        This is because the arkad.Router is a subclass of the ninja.Router, and we want to make sure
        that we are using the correct one which auto enables by_alias.
        """
        return super().add_router(
            prefix,
            router,
            auth=auth,
            throttle=throttle,
            tags=tags,
            parent_router=parent_router,
        )


api = CustomNinjaAPI(
    title="Arkad API",
    docs=Swagger(settings={"persistAuthorization": True}),
    auth=AuthBearer(),
    default_router=Router(),
)
api.add_router("user", user_router)
api.add_router("student-session", student_sessions_router)
api.add_router("company", company_router)
api.add_router("events", event_booking_router)


@api.exception_handler(jwt.InvalidKeyError)
@api.exception_handler(jwt.InvalidTokenError)
def on_invalid_token(request: HttpRequest, exc: Exception) -> HttpResponse:
    return api.create_response(
        request, {"detail": "Invalid token supplied"}, status=401
    )


@api.exception_handler(jwt.ExpiredSignatureError)
def on_expired_token(request: HttpRequest, exc: Exception) -> HttpResponse:
    return api.create_response(
        request, {"detail": "Expired token supplied"}, status=401
    )


@api.exception_handler(jwt.InvalidAlgorithmError)
def on_invalid_algorithm(request: HttpRequest, exc: Exception) -> HttpResponse:
    return api.create_response(request, {"detail": "Invalid token"}, status=401)


@api.get(
    "get-public-key", response={200: PublicKeySchema}, auth=None, tags=["Cryptography"]
)
def get_public_key(request: AuthenticatedRequest):
    if not PUBLIC_KEY.strip().startswith(
        "-----BEGIN PUBLIC KEY-----"
    ) or not PUBLIC_KEY.strip().endswith("-----END PUBLIC KEY-----"):
        raise jwt.InvalidTokenError("Something went very wrong")

    return PublicKeySchema(public_key=PUBLIC_KEY)
