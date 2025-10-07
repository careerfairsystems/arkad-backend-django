from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login

from user_models.models import User, StaffEnrollmentToken, StaffEnrollmentUsage
from user_models.schema import SignupSchema
from user_models.api import begin_signup


@login_required
@require_http_methods(["GET", "POST"])
def delete_account(request: HttpRequest) -> HttpResponse:
    """
    Allow users to delete their account and all associated data.
    Staff and company users can view the page but cannot delete their accounts - they must contact a superadmin.
    """
    user: User = request.user  # type: ignore

    # Prevent staff users and company users from deleting their accounts via POST
    if request.method == "POST":
        if user.is_staff or user.is_company:
            messages.error(
                request,
                "Staff and company users cannot delete their accounts through this interface. Please contact a superadmin.",
            )
            return redirect(reverse("delete_account"))

        # Delete the user and all associated data
        user.delete()
        messages.success(request, "Your account has been successfully deleted.")
        return redirect("/")

    # GET request - show the confirmation page
    # Pass a flag to indicate if user can delete their account
    can_delete = not (user.is_staff or user.is_company)
    return render(
        request, "delete_account.html", {"user": user, "can_delete": can_delete}
    )


@require_http_methods(["GET"])
def staff_enrollment(request: HttpRequest, token: str) -> HttpResponse:
    """
    Staff enrollment landing page - verifies token and shows signup form.
    Uses the same email verification flow as regular signup.
    """
    # Verify token exists and is valid FIRST
    try:
        enrollment_token = StaffEnrollmentToken.objects.get(token=token)
    except StaffEnrollmentToken.DoesNotExist:
        messages.error(request, "Invalid enrollment link.")
        return redirect(reverse("login"))

    # Check if token is still valid
    if not enrollment_token.is_valid():
        if not enrollment_token.is_active:
            messages.error(request, "This enrollment link has been deactivated.")
        else:
            messages.error(request, "This enrollment link has expired.")
        return redirect(reverse("login"))

    # Store token in session for the signup process
    request.session["staff_enrollment_token"] = token

    # Show the enrollment form
    return render(request, "staff_enrollment.html", {"token": token})


@require_http_methods(["POST"])
def staff_begin_signup(request: HttpRequest) -> HttpResponse:
    """
    Begin staff signup with email verification - proxies to the existing begin_signup API.
    """
    # Get the enrollment token from session
    enrollment_token_str = request.session.get("staff_enrollment_token")
    if not enrollment_token_str:
        messages.error(
            request, "Invalid enrollment session. Please use the enrollment link again."
        )
        return redirect(reverse("login"))

    # Verify token is still valid
    try:
        enrollment_token = StaffEnrollmentToken.objects.get(token=enrollment_token_str)
    except StaffEnrollmentToken.DoesNotExist:
        messages.error(request, "Invalid enrollment link.")
        return redirect(reverse("login"))

    if not enrollment_token.is_valid():
        messages.error(request, "This enrollment link is no longer valid.")
        return redirect(reverse("login"))

    # Get form data
    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "")
    first_name = request.POST.get("first_name", "").strip()
    last_name = request.POST.get("last_name", "").strip()

    # Create SignupSchema and call the existing begin_signup function
    signup_data = SignupSchema(
        email=email,
        password=password,
        first_name=first_name or None,
        last_name=last_name or None,
        food_preferences=None,
    )

    # Call the existing begin_signup API
    status_code, result = begin_signup(request, signup_data)

    if status_code == 200:
        # Store the JWT token, signup data, and complete form data in session
        request.session["verification_token"] = result
        request.session["signup_email"] = email
        request.session["complete_signup_data"] = {
            "email": email,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "food_preferences": None,
        }
        messages.success(request, f"Verification code sent to {email}")
        return render(
            request,
            "staff_enrollment_verify.html",
            {
                "token": enrollment_token_str,
                "email": email,
            },
        )
    else:
        # Handle errors
        messages.error(request, result)
        return render(
            request,
            "staff_enrollment.html",
            {
                "token": enrollment_token_str,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
            },
        )


@require_http_methods(["POST"])
def staff_complete_signup(request: HttpRequest) -> HttpResponse:
    """
    Complete staff signup after email verification - proxies to existing complete_signup API
    and then upgrades the user to staff.
    """
    # Get data from session
    verification_token = request.session.get("verification_token")
    signup_email = request.session.get("signup_email")
    enrollment_token_str = request.session.get("staff_enrollment_token")

    if not all([verification_token, signup_email, enrollment_token_str]):
        messages.error(request, "Invalid signup session. Please start again.")
        return redirect(reverse("login"))

    # Verify enrollment token is still valid
    try:
        enrollment_token = StaffEnrollmentToken.objects.get(token=enrollment_token_str)
    except StaffEnrollmentToken.DoesNotExist:
        messages.error(request, "Invalid enrollment link.")
        return redirect(reverse("login"))

    if not enrollment_token.is_valid():
        messages.error(request, "This enrollment link is no longer valid.")
        return redirect(reverse("login"))

    # Get verification code from form
    code = request.POST.get("code", "").strip()

    # Verify the 2FA code using the same logic as the API
    from arkad.jwt_utils import jwt_decode
    from hashlib import sha256
    from arkad.settings import SECRET_KEY
    from django.db import IntegrityError

    try:
        jwt_data = jwt_decode(verification_token)
    except Exception:
        messages.error(request, "Invalid or expired verification token.")
        return redirect(reverse("login"))

    # Verify the 2FA code
    if (
        jwt_data["code2fa"]
        != sha256((SECRET_KEY + jwt_data["salt2fa"] + code).encode("utf-8")).hexdigest()
    ):
        messages.error(request, "Invalid verification code.")
        return render(
            request,
            "staff_enrollment_verify.html",
            {
                "token": enrollment_token_str,
                "email": signup_email,
            },
        )

    # Get the stored complete signup data from session
    stored_signup_data = request.session.get("complete_signup_data")
    if not stored_signup_data:
        messages.error(
            request, "Session expired. Please start the signup process again."
        )
        return redirect(
            reverse("staff_enrollment", kwargs={"token": enrollment_token_str})
        )

    # Create the user with staff privileges
    try:
        user = User.objects.create_user(
            username=stored_signup_data["email"],
            email=stored_signup_data["email"],
            password=stored_signup_data["password"],
            first_name=stored_signup_data.get("first_name") or "",
            last_name=stored_signup_data.get("last_name") or "",
            food_preferences=stored_signup_data.get("food_preferences"),
            is_staff=True,
            is_student=False,
        )

        # Track the usage
        StaffEnrollmentUsage.objects.create(token=enrollment_token, user=user)

        # Clear session data
        request.session.pop("verification_token", None)
        request.session.pop("signup_email", None)
        request.session.pop("staff_enrollment_token", None)
        request.session.pop("complete_signup_data", None)

        # Log the user in
        login(request, user)

        messages.success(
            request,
            f"Welcome {user.first_name or user.username}! Your staff account has been created successfully.",
        )
        return redirect("/admin/")

    except IntegrityError:
        messages.error(request, "A user with this email already exists.")
        return redirect(reverse("login"))
