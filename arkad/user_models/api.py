from django.contrib.auth import authenticate, login
from django.http import HttpRequest
from ninja import Router, Schema

from arkad.user_models.models import User

api = Router()

class SigninSchema(Schema):
    username: str
    password: str

@api.post('signin', auth=None, response={401: str, 200: str})
def signin(request: HttpRequest, data: SigninSchema):
    user: User | None = authenticate(request=request, **data)
    if user is None:
        return 401, "Invalid username or password"
    login(request, user)
    return 200, user.create_jwt_token()
