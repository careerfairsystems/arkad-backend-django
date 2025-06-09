from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


def send_signup_code_email(email: str, code: str) -> None:
    """
    Send a signup code email to the user.

    Renders the email template with digits being the 6-digit code.
    """

    # Ensure the code is a 6-digit string
    if len(code) != 6 or not code.isdigit():
        raise ValueError("Code must be a 6-digit string.")

    subject: str = "Your Arkad Signup Code"
    message: str = render_to_string("email_app/sign_up.html", {"digits": list(code)})
    from_email: str = settings.DEFAULT_FROM_EMAIL
    recipient_list: list[str] = [email, ]
    send_mail(
        subject=subject,
        message=f"Your signup code is {code}. "
                f"This is a plain text version of the email. "
                f"Please enable HTML to view the full content.",
        html_message=message,
        from_email=from_email,
        recipient_list=recipient_list,
        fail_silently=False,
    )
