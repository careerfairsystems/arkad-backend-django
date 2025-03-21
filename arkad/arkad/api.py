from django.http import HttpRequest, HttpResponse
from ninja import NinjaAPI, Swagger
from ninja.security import HttpBearer
import jwt

from .settings import SECRET_KEY
from user_models.models import User
from user_models.api import router as user_router
from student_sessions.api import router as student_sessions_router
from companies.api import router as company_router
from event_booking.api import router as event_booking_router


class AuthBearer(HttpBearer):
    def authenticate(self, request: HttpRequest, token: str) -> User:
        # Implement authentication
        decoded: dict = jwt.decode(token, SECRET_KEY, algorithms=["HS512"])
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
def on_invalid_token(request: HttpRequest, exc: Exception) -> HttpResponse:
    return api.create_response(
        request, {"detail": "Invalid token supplied"}, status=401
    )


@api.exception_handler(jwt.ExpiredSignatureError)
def on_expired_token(request: HttpRequest, exc: Exception) -> HttpResponse:
    return api.create_response(
        request, {"detail": "Expired token supplied"}, status=401
    )
