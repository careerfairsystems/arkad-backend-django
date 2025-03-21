import logging

from django.contrib.auth import authenticate, login
from django.db import IntegrityError
from django.http import HttpRequest
from ninja import Router, File, UploadedFile, PatchDict

from user_models.models import User
from user_models.schema import (
    SigninSchema,
    ProfileSchema,
    SignupSchema,
    UpdateProfileSchema,
)


auth = Router(tags=["Authentication"])
profile = Router(tags=["User Profile"])
router = Router(tags=["Users"])
router.add_router("", auth)
router.add_router("profile", profile)


@auth.post("signup", auth=None, response={200: ProfileSchema, 400: str})
def signup(request: HttpRequest, data: SignupSchema):
    """
    This endpoint creates a user with the given information.

    username, password are required.
    Returns user information if successful. Call signin with the username and password to retrieve a JWT.
    """
    try:
        # TODO enable password requirements! Important
        return 200, User.objects.create_user(**data.model_dump())
    except IntegrityError as e:
        logging.error(e)
        if "duplicate key" in str(e):
            return 400, "Username already exists"
        else:
            return 500, "Something went wrong"


@auth.post("signin", auth=None, response={401: str, 200: str})
def signin(request: HttpRequest, data: SigninSchema):
    """
    Returns a users JWT token when given a correct username and password.
    """

    user: User | None = authenticate(request=request, **data.model_dump())
    if user is None:
        return 401, "Invalid username or password"
    login(request, user)
    return 200, user.create_jwt_token()


@profile.get("", response={200: ProfileSchema})
def get_user_profile(request: HttpRequest):
    """
    Returns the users profile information.
    """
    return request.user


@profile.put("", response={200: ProfileSchema})
def update_profile(request: HttpRequest, data: UpdateProfileSchema):
    """
    Replaces the users profile information to the given information.
    """
    user = request.user
    user.email = data.email
    user.first_name = data.first_name
    user.last_name = data.last_name
    user.programme = data.programme
    user.linkedin = data.linkedin
    user.master_title = data.master_title
    user.study_year = data.study_year
    user.save()
    return ProfileSchema.from_orm(user)


@profile.patch("", response={200: ProfileSchema})
def update_profile_fields(request: HttpRequest, data: PatchDict[UpdateProfileSchema]):
    """
    Updates the users profile information with the given, (not null) data.
    """
    user: User = request.user
    for attr, value in data.items():
        setattr(user, attr, value)
    user.save()
    return ProfileSchema.from_orm(user)


@profile.post("profile-picture", response={200: str})
def update_profile_picture(
    request: HttpRequest, profile_picture: UploadedFile = File(...)
):
    """
    Update the profile picture to a new one.
    Deletes the old profile picture.
    """

    request.user.profile_picture.delete()
    request.user.profile_picture = profile_picture
    request.user.save()
    return 200, "Profile picture updated"


@profile.delete("profile-picture", response={200: str})
def delete_profile_picture(request: HttpRequest):
    """
    Returns 200 if the file was deleted. Will also return 200 if the file never existed.
    """
    request.user.profile_picture.delete()
    request.user.save()
    return 200, "Profile picture deleted"


@profile.post("cv", response={200: str})
def update_cv(request: HttpRequest, cv: UploadedFile = File(...)):
    """
    Update the cv to a new one.
    Deletes the old cv.
    """
    request.user.cv.delete()
    request.user.cv = cv
    request.user.save()
    return 200, "CV updated"


@profile.delete("cv", response={200: str})
def delete_cv(request: HttpRequest):
    """
    Returns 200 if the cv was deleted. Will also return 200 if the file never existed.
    """
    request.user.cv.delete()
    request.user.save()
    return 200, "CV deleted"
