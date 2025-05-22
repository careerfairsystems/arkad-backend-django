import base64
import logging
import os
import secrets

from django.contrib.auth import authenticate, login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import HttpRequest
from ninja import File, UploadedFile, PatchDict

from arkad.customized_django_ninja import Router
from arkad.email_utils import send_mail
from arkad.jwt_utils import jwt_encode, jwt_decode
from arkad.settings import SECRET_KEY
from user_models.models import User, AuthenticatedRequest, Favourites
from user_models.schema import (
    SigninSchema,
    ProfileSchema,
    SignupSchema,
    UpdateProfileSchema,
    CompleteSignupSchema,
    ResetPasswordSchema,
)
from hashlib import sha256
from companies.models import Company



auth = Router(tags=["Authentication"])
profile = Router(tags=["User Profile"])
router = Router(tags=["Users"])
router.add_router("", auth)
router.add_router("profile", profile)


@auth.post("begin-signup", auth=None, response={200: str, 400: str, 415: str})
def begin_signup(request: AuthenticatedRequest, data: SignupSchema):
    """
    This endpoint begins the account creation process, returns a jwt which has to be used again with a 2fa code.

    """

    def generate_salt(length: int = 16) -> str:
        return base64.b64encode(os.urandom(length)).decode("utf-8")

    try:
        validate_password(data.password)
    except ValidationError as e:
        return 415, "\n".join(e.messages)

    if User.objects.filter(email=data.email, username=data.email).exists():
        return 415, "User with this email already exists."

    # 6 random numbers
    code: str = str(secrets.randbelow(1000000))
    code = ("0" * (6 - len(code)) + code)[:6]
    salt: str = generate_salt()
    # Send 2fa code
    send_mail(data.email, code, code, code)  # TODO: Make this nice
    return 200, jwt_encode(
        {
            "code2fa": sha256(
                (SECRET_KEY + salt + code).encode("utf-8"), usedforsecurity=True
            ).hexdigest(),
            "salt2fa": salt,
            "signup-data-hash": sha256(
                data.model_dump_json().encode("utf-8"), usedforsecurity=False
            ).hexdigest(),
        }
    )


@auth.post(
    "complete-signup", auth=None, response={200: ProfileSchema, 401: str, 400: str}
)
def complete_signup(request: AuthenticatedRequest, data: CompleteSignupSchema):
    """
    Complete the signup process, must be given the same data as in begin signup, the 2fa code and the token
    received when beginning signup
    """
    jwt_data: dict[str, str] = jwt_decode(data.token)
    if (
        jwt_data["code2fa"]
        != sha256(
            (SECRET_KEY + jwt_data["salt2fa"] + data.code).encode("utf-8")
        ).hexdigest()
    ):
        return 401, "Non matching 2fa codes"
    signup_schema: SignupSchema = SignupSchema(**data.model_dump())
    signup_data_hash_current: str = sha256(
        signup_schema.model_dump_json().encode("utf-8"), usedforsecurity=False
    ).hexdigest()
    signup_data_hash: str | None = jwt_data.get("signup-data-hash", None)
    if signup_data_hash is None:
        return 401, "Signup data hash was empty"
    if signup_data_hash != signup_data_hash_current:
        return 401, "Signup data hash does not match"

    try:
        # We should not need any validations here, do it in begin_signup
        return 200, User.objects.create_user(
            **signup_schema.model_dump(), username=data.email
        )
    except IntegrityError as e:
        logging.error(e)
        if "duplicate key" in str(e):
            return 400, "Email already exists"
        else:
            return 500, "Something went wrong"


@auth.post("signin", auth=None, response={401: str, 200: str})
def signin(request: HttpRequest, data: SigninSchema):
    """
    Returns a users JWT token when given a correct username and password.
    """

    user: User | None = authenticate(
        request=request, **data.model_dump(), username=data.email
    )

    if user is None:
        return 401, "Invalid email or password"
    login(request, user)
    return 200, user.create_jwt_token()


@auth.post("reset-password", auth=None, response={200: str})
def reset_password(request:HttpRequest, data:ResetPasswordSchema):
    """
    Just for testing purposes atm. Only returns response 200.
    """

    return 200, "Ok"


@profile.get("", response={200: ProfileSchema})
def get_user_profile(request: AuthenticatedRequest):
    """
    Returns the users profile information.
    """
    return request.user


@profile.put("", response={200: ProfileSchema})
def update_profile(request: AuthenticatedRequest, data: UpdateProfileSchema):
    """
    Replaces the users profile information to the given information.
    """
    user = request.user
    user.first_name = data.first_name  # type: ignore[assignment]
    user.last_name = data.last_name  # type: ignore[assignment]
    user.programme = data.programme
    user.linkedin = data.linkedin
    user.master_title = data.master_title
    user.study_year = data.study_year
    user.food_preferences = data.food_preferences
    user.save()
    return ProfileSchema.from_orm(user)


@profile.patch("", response={200: ProfileSchema})
def update_profile_fields(request: AuthenticatedRequest, data: PatchDict[UpdateProfileSchema]):  # type: ignore[type-arg]
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
    request: AuthenticatedRequest, profile_picture: UploadedFile = File(...)  # type: ignore[type-arg]
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
def delete_profile_picture(request: AuthenticatedRequest):
    """
    Returns 200 if the file was deleted. Will also return 200 if the file never existed.
    """
    request.user.profile_picture.delete()
    request.user.save()
    return 200, "Profile picture deleted"


@profile.post("cv", response={200: str})
def update_cv(request: AuthenticatedRequest, cv: UploadedFile = File(...)):  # type: ignore[type-arg]
    """
    Update the cv to a new one.
    Deletes the old cv.
    """
    request.user.cv.delete()
    request.user.cv = cv
    request.user.save()
    return 200, "CV updated"


@profile.delete("cv", response={200: str})
def delete_cv(request: AuthenticatedRequest):
    """
    Returns 200 if the cv was deleted. Will also return 200 if the file never existed.
    """
    request.user.cv.delete()
    request.user.save()
    return 200, "CV deleted"




@profile.post("favourite", response={200: str, 400:str})
def add_favourite(request: AuthenticatedRequest, company_id: int):  # type: ignore[type-arg]
    """
     Returns 200 if a company is added as a favourite
     Returns 400 if duplicate
    """

    try:
        company = Company.objects.get(id=company_id)
        fave = Favourites.objects.create(company = company, user = request.user)
        return 200, "favourite added"
    except IntegrityError as e:
        logging.error(e)
        if "duplicate key" in str(e):
            return 400, "Company already exists"
        

#se om man likeat ett företag




