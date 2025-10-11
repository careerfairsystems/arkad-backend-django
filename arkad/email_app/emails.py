from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpRequest
from django.template.loader import render_to_string
import re

from email_app.utils import get_base_url, get_base_url_from_settings


def send_signup_code_email(request: HttpRequest, email: str, code: str) -> None:
    """
    Send a signup code email to the user.

    Renders the email template with digits being the 6-digit code.

    Args:
        request: HttpRequest object to get the base URL
        email: Recipient email address
        code: 6-digit signup code
    """
    # Ensure the code is a 6-digit string
    if len(code) != 6 or not code.isdigit():
        raise ValueError("Code must be a 6-digit string.")

    subject: str = "Your Arkad Signup Code"
    message: str = render_to_string(
        "email_app/sign_up.html",
        {"digits": list(code), "base_url": get_base_url(request)},
    )
    from_email: str = settings.DEFAULT_FROM_EMAIL
    recipient_list: list[str] = [email]

    plain_text = (
        f"Your signup code is {code}. "
        f"This is a plain text version of the email. "
        f"Please enable HTML to view the full content."
    )

    send_mail(
        subject=subject,
        message=plain_text,
        html_message=message,
        from_email=from_email,
        recipient_list=recipient_list,
        fail_silently=False,
    )


def send_generic_information_email(
    email: str,
    subject: str,
    name: str = "",
    greeting: str = "",
    heading: str = "",
    message: str = "",
    button_text: str = "",
    button_link: str = "",
    note: str = "",
    request: HttpRequest | None = None,
) -> None:
    """
    Send a generic information email to the user.

    Args:
        email: Recipient email address
        subject: Email subject line
        name: Recipient name (used in default greeting if greeting not provided)
        greeting: Custom greeting text (optional, defaults to "Hello {name}!")
        heading: Subheading text (optional)
        message: Main message content (supports HTML) (optional)
        button_text: Text for the call-to-action button (optional)
        button_link: URL for the call-to-action button (optional)
        note: Footer note text (optional)
        request: HttpRequest object to get the base URL (optional)
    """
    base_url = get_base_url(request) if request else get_base_url_from_settings()
    html_message: str = render_to_string(
        "email_app/generic_information_email.html",
        {
            "name": name,
            "greeting": greeting,
            "heading": heading,
            "message": message,
            "button_text": button_text,
            "button_link": button_link,
            "note": note,
            "base_url": base_url,
        },
    )

    # Create a plain text version by stripping HTML tags
    plain_text_message = f"{greeting or f'Hello {name}!'}\n\n"
    if heading:
        plain_text_message += f"{heading}\n\n"
    if message:
        # Basic HTML stripping for plain text
        plain_text_message += re.sub("<[^<]+?>", "", message) + "\n\n"
    if button_text and button_link:
        plain_text_message += f"{button_text}: {button_link}\n\n"
    if note:
        plain_text_message += f"{note}\n"

    from_email: str = settings.DEFAULT_FROM_EMAIL
    recipient_list: list[str] = [email]

    send_mail(
        subject=subject,
        message=plain_text_message,
        html_message=html_message,
        from_email=from_email,
        recipient_list=recipient_list,
        fail_silently=False,
    )
