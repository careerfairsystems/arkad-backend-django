import base64
import logging
import os
import secrets

from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import HttpRequest
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from ninja import File, UploadedFile, PatchDict
from arkad.customized_django_ninja import Router
from arkad.jwt_utils import jwt_encode, jwt_decode
from arkad.settings import SECRET_KEY
from email_app.emails import send_signup_code_email
from email_app.utils import get_base_url
from user_models.models import User, AuthenticatedRequest
from user_models.schema import (
    SigninSchema,
    ProfileSchema,
    SignupSchema,
    UpdateProfileSchema,
    CompleteSignupSchema,
    ResetPasswordSchema,
    ValidateTokenSchema,
    StaffBeginSignupSchema,
    StaffCompleteSignupSchema,
)
from hashlib import sha256


auth = Router(tags=["Authentication"])
profile = Router(tags=["User Profile"])
staff_enrollment = Router(tags=["Staff Enrollment"])
router = Router(tags=["Users"])
router.add_router("", auth)
router.add_router("profile", profile)
router.add_router("staff-enrollment", staff_enrollment)


@auth.post("begin-signup", auth=None, response={200: str, 415: str, 429: str, 409: str})
def begin_signup(request: HttpRequest, data: SignupSchema):
    """
    This endpoint begins the account creation process, returns a jwt which has to be used again with a 2fa code.

    Only allowing sending an email once every 30 seconds to prevent abuse. If in that window 429 is returned.
    409 is returned if the user already exists.
    """

    def generate_salt(length: int = 16) -> str:
        return base64.b64encode(os.urandom(length)).decode("utf-8")

    try:
        validate_password(data.password)
    except ValidationError as e:
        return 415, "\n".join(e.messages)

    if User.objects.filter(email=data.email, username=data.email).exists():
        return 409, "User with this email already exists."

    key: str = f"signup-{data.email}"

    ratelimited: bool = cache.get(key, False)
    if ratelimited:
        return (
            429,
            "You have already requested a signup code, please wait before trying again.",
        )
    # 6 random numbers
    code: str = str(secrets.randbelow(1000000))
    code = ("0" * (6 - len(code)) + code)[:6]
    salt: str = generate_salt()
    # Send 2fa code
    send_signup_code_email(request, email=data.email, code=code)
    cache.set(key, True, timeout=30)
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


@auth.post("ws-token", response={200: str, 401: str})
def get_ws_token(request: AuthenticatedRequest):
    """
    Exchange bearer token for WebSocket token with shorter expiry.
    """
    # Create a WebSocket-specific token with shorter expiry (30 minutes)
    return 200, jwt_encode(
        {"user_id": request.user.id, "token_type": "websocket"}, expiry_minutes=30
    )


@auth.post("reset-password", auth=None, response={200: str, 429: str})
def reset_password(request: HttpRequest, data: ResetPasswordSchema):
    """
    Sends an email with a link to reset password. Always returns 200 (or 500).
    Returns 429 if the user has requested a reset within the last 30 seconds.
    """
    key: str = f"reset-password-{data.email}"
    ratelimited: bool = cache.get(key, False)
    if ratelimited:
        return (
            429,
            "You have already requested a password reset, please wait before trying again.",
        )

    form = PasswordResetForm(data={"email": data.email})

    if form.is_valid():
        User = get_user_model()

        try:
            user = User.objects.get(email=data.email)

            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            relative_url = reverse(
                "password_reset_confirm", kwargs={"uidb64": uidb64, "token": token}
            )

            reset_link = request.build_absolute_uri(relative_url)

            form.save(
                request=request,
                use_https=request.is_secure(),
                from_email="Arkad No Reply <no-reply@arkadtlth.se>",
                email_template_name="registration/password_reset_email.html",
                subject_template_name="registration/password_reset_subject.txt",
                html_email_template_name="email_app/reset.html",
                extra_email_context={
                    "reset_link": reset_link,
                    "name": user.first_name,
                    "base_url": get_base_url(request),
                },
            )
            cache.set(key, True, timeout=30)

        except User.DoesNotExist:
            pass

    return 200, "OK"


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
def update_profile_fields(
    request: AuthenticatedRequest, data: PatchDict[UpdateProfileSchema]
):  # type: ignore[type-arg]
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
    request: AuthenticatedRequest,
    profile_picture: UploadedFile = File(...),  # type: ignore[type-arg]
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


# Staff Enrollment API endpoints
@staff_enrollment.post(
    "validate-token", auth=None, response={200: dict, 400: str, 404: str}
)
def validate_enrollment_token(request: HttpRequest, data: ValidateTokenSchema):
    """
    Validate a staff enrollment token.
    Returns token details if valid, error message otherwise.
    """
    from user_models.models import StaffEnrollmentToken

    try:
        token = StaffEnrollmentToken.objects.get(token=data.token)
    except StaffEnrollmentToken.DoesNotExist:
        return 404, "Invalid enrollment token"

    if not token.is_valid():
        if not token.is_active:
            return 400, "This enrollment token has been deactivated"
        else:
            return 400, "This enrollment token has expired"

    return 200, {
        "valid": True,
        "expires_at": token.expires_at.isoformat(),
        "created_by": token.created_by.username,
    }


@staff_enrollment.post(
    "begin-signup",
    auth=None,
    response={200: str, 400: str, 404: str, 415: str, 429: str},
)
def staff_begin_signup(request: HttpRequest, data: StaffBeginSignupSchema):
    """
    Begin staff signup with email verification.
    Validates enrollment token and proxies to regular signup flow.
    Returns JWT verification token on success.
    """
    from user_models.models import StaffEnrollmentToken

    # Validate enrollment token first
    try:
        enrollment_token = StaffEnrollmentToken.objects.get(token=data.enrollment_token)
    except StaffEnrollmentToken.DoesNotExist:
        return 404, "Invalid enrollment token"

    if not enrollment_token.is_valid():
        if not enrollment_token.is_active:
            return 400, "This enrollment token has been deactivated"
        else:
            return 400, "This enrollment token has expired"

    # Create signup schema and call existing begin_signup
    signup_data = SignupSchema(
        email=data.email,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
        food_preferences=None,
    )

    # Call the existing begin_signup function
    status_code, result = begin_signup(request, signup_data)
    if status_code != 200:
        return status_code, result

    # result is a JWT token - mark it as used for staff enrollment
    # Store the enrollment token association, not just a boolean
    cache.set(f"staff-enrollment-{result}", data.enrollment_token, timeout=600)
    return status_code, result


@staff_enrollment.post(
    "complete-signup",
    auth=None,
    response={200: ProfileSchema, 400: str, 401: str, 404: str},
)
def staff_complete_signup(request: HttpRequest, data: StaffCompleteSignupSchema):
    """
    Complete staff signup after email verification.
    Creates user with staff privileges and tracks enrollment usage.
    Works like normal signup - validates data hash against JWT.
    """
    from user_models.models import StaffEnrollmentToken, StaffEnrollmentUsage

    # Validate enrollment token
    try:
        enrollment_token = StaffEnrollmentToken.objects.get(token=data.enrollment_token)  # type: ignore[attr-defined]
    except StaffEnrollmentToken.DoesNotExist:
        return 404, "Invalid enrollment token"

    if not enrollment_token.is_valid():
        if not enrollment_token.is_active:
            return 400, "This enrollment token has been deactivated"
        else:
            return 400, "This enrollment token has expired"

    # Verify that the signup processes was also started as a staff enrollment:
    if not cache.get(f"staff-enrollment-{data.verification_token}", False):
        return 401, "Invalid or expired verification token"

    # Verify the 2FA code from the verification token
    try:
        jwt_data = jwt_decode(data.verification_token)
    except Exception:
        return 401, "Invalid or expired verification token"

    # Verify the 2FA code
    if (
        jwt_data["code2fa"]
        != sha256(
            (SECRET_KEY + jwt_data["salt2fa"] + data.code).encode("utf-8")
        ).hexdigest()
    ):
        return 401, "Invalid verification code"

    # Create SignupSchema from the data to validate against the hash
    signup_schema = SignupSchema(
        email=data.email,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
        food_preferences=None,
    )

    # Verify the signup data hash matches what was sent in begin-signup
    signup_data_hash_current = sha256(
        signup_schema.model_dump_json().encode("utf-8"), usedforsecurity=False
    ).hexdigest()
    signup_data_hash = jwt_data.get("signup-data-hash")

    if not signup_data_hash:
        return 401, "Signup data hash was empty"

    if signup_data_hash != signup_data_hash_current:
        return 401, "Signup data does not match"

    # Create the user with staff privileges
    try:
        user = User.objects.create_user(
            username=data.email,
            email=data.email,
            password=data.password,
            first_name=data.first_name or "",
            last_name=data.last_name or "",
            food_preferences=None,
            is_staff=True,
            is_student=False,
        )

        # Track the usage
        StaffEnrollmentUsage.objects.create(token=enrollment_token, user=user)  # type: ignore[attr-defined]

        # Log the user in
        login(request, user)

        return 200, ProfileSchema.from_orm(user)

    except IntegrityError as e:
        logging.error(e)
        if "duplicate key" in str(e):
            return 400, "Email already exists"
        else:
            return 500, "Something went wrong"
