from django.contrib.auth import authenticate, login
from django.http import HttpRequest
from ninja import Router

from user_models.models import User
from user_models.schema import SigninSchema, ProfileSchema

router = Router()


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