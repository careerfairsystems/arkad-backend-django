from django.contrib.auth import authenticate, login
from django.db import IntegrityError
from django.http import HttpRequest
from ninja import Router

from user_models.models import User
from user_models.schema import SigninSchema, ProfileSchema, SignupSchema

router = Router()


@router.post("signup", auth=None, response={200: ProfileSchema, 400: str})
def signup(request: HttpRequest, data: SignupSchema):
    try:
        return 200, User.objects.create_user(
            username=data.username,
            email=data.email,
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name,
        )
    except IntegrityError:
        return 400, "Username already exists"

@router.post('signin', auth=None, response={401: str, 200: str})
def signin(request: HttpRequest, data: SigninSchema):
    user: User | None = authenticate(request=request, **data.model_dump())
    if user is None:
        return 401, "Invalid username or password"
    login(request, user)
    return 200, user.create_jwt_token()

@router.get("profile", response={200: ProfileSchema})
def get_user_profile(request: HttpRequest):
    return request.user
