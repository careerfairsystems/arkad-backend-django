from django.contrib.auth import authenticate, login
from django.db import IntegrityError
from django.http import HttpRequest
from ninja import Router

from user_models.models import User
from user_models.schema import SigninSchema, ProfileSchema, SignupSchema

router = Router()


@router.post("signup", auth=None, response={200: ProfileSchema, 400: str})
def signup(request: HttpRequest, data: SignupSchema):
    """
    This endpoint creates a user with the given information.

    username, password are required.
    Returns user information if successful. Call signin with the username and password to retrieve a JWT.
    """
    try:
        return 200, User.objects.create_user(
            **data.model_dump()
        )
    except IntegrityError:
        return 400, "Username already exists"

@router.post('signin', auth=None, response={401: str, 200: str})
def signin(request: HttpRequest, data: SigninSchema):
    """
    Returns a users JWT token when given a correct username and password.
    """

    user: User | None = authenticate(request=request, **data.model_dump())
    if user is None:
        return 401, "Invalid username or password"
    login(request, user)
    return 200, user.create_jwt_token()

@router.get("profile", response={200: ProfileSchema})
def get_user_profile(request: HttpRequest):
    """
    Returns the users profile information.
    """
    return request.user
