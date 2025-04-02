from django.http import HttpRequest, HttpResponse
from ninja import NinjaAPI, Swagger
from ninja.security import HttpBearer
import jwt
from pydantic import BaseModel

from .jwt_utils import jwt_decode, PUBLIC_KEY, PublicKeySchema
from user_models.models import User
from user_models.api import router as user_router
from student_sessions.api import router as student_sessions_router
from companies.api import router as company_router
from event_booking.api import router as event_booking_router


class AuthenticatedRequest(BaseModel):
    user: User

class AuthBearer(HttpBearer):
    def authenticate(self, request: AuthenticatedRequest, token: str) -> User:
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

api = NinjaAPI(
    title="Arkad API",
    docs=Swagger(settings={"persistAuthorization": True}),
    auth=AuthBearer(),
)
api.add_router("user", user_router)
api.add_router("student-session", student_sessions_router)
api.add_router("company", company_router)
api.add_router("events", event_booking_router)


@api.exception_handler(jwt.InvalidKeyError)
def on_invalid_token(request: AuthenticatedRequest, exc: Exception) -> HttpResponse:
    return api.create_response(
        request, {"detail": "Invalid token supplied"}, status=401
    )


@api.exception_handler(jwt.ExpiredSignatureError)
def on_expired_token(request: AuthenticatedRequest, exc: Exception) -> HttpResponse:
    return api.create_response(
        request, {"detail": "Expired token supplied"}, status=401
    )


@api.get(
    "get-public-key", response={200: PublicKeySchema}, auth=None, tags=["Cryptography"]
)
def get_public_key(request: AuthenticatedRequest):
    if not PUBLIC_KEY.strip().startswith(
        "-----BEGIN PUBLIC KEY-----"
    ) or not PUBLIC_KEY.strip().endswith("-----END PUBLIC KEY-----"):
        raise jwt.InvalidTokenError("Something went very wrong")

    return PublicKeySchema(public_key=PUBLIC_KEY)
