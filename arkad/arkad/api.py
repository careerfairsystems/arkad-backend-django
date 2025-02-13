from django.http import HttpRequest, HttpResponse
from ninja import NinjaAPI, Swagger
from ninja.security import HttpBearer
import jwt

from .settings import SECRET_KEY
from user_models.models import User


class AuthBearer(HttpBearer):
    def authenticate(self, request: HttpRequest, token: str) -> None:
        # Implement authentication
        decoded: dict = jwt.decode(token, SECRET_KEY, algorithms=["HS512"])
        print("Authenticated ", decoded["id"])
        request.user = User.objects.get(id=decoded["id"])

api = NinjaAPI(docs=Swagger(settings={"persistAuthorization": True}), auth=AuthBearer())

@api.exception_handler(jwt.InvalidKeyError)
def on_invalid_token(request: HttpRequest, exc: Exception) -> HttpResponse:
    return api.create_response(request, {"detail": "Invalid token supplied"}, status=401)

@api.exception_handler(jwt.ExpiredSignatureError)
def on_invalid_token(request: HttpRequest, exc: Exception) -> HttpResponse:
    return api.create_response(request, {"detail": "Expired token supplied"}, status=401)
