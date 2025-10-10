from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpRequest
from django.template.loader import render_to_string
from datetime import datetime
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


def send_event_closing_reminder_email(
    email: str,
    event_name: str,
    company_name: str,
    event_type: str,
    closes_at: datetime,
    event_description: str = "",
    location: str | None = "",
    button_link: str = "",
    disclaimer: str | None = "",
    request: HttpRequest | None = None,
) -> None:
    """
    Send a reminder email that event registration closes tomorrow.

    Args:
        email: Recipient email address
        event_name: Name of the event
        company_name: Name of the company
        event_type: Type of event (e.g., 'Lunch', 'Company Visit', 'Student Session')
        closes_at: When registration closes
        event_description: Description of the event
        location: Event location
        button_link: Link to manage booking
        disclaimer: Special disclaimer (e.g., for SAAB, FMV)
        request: HttpRequest object to get the base URL (optional)
    """
    subject = f"Registration for {event_type} with {company_name} closes tomorrow"
    greeting = "Reminder!"
    heading = "Registration closes tomorrow"
    message = (
        f"Remember to cancel your spot if you can't attend! "
        f"Registration closes on {closes_at.strftime('%Y-%m-%d at %H:%M')}."
    )
    button_text = "Manage my booking"

    event_date = closes_at.strftime("%Y-%m-%d")

    base_url = get_base_url(request) if request else get_base_url_from_settings()
    html_message = render_to_string(
        "email_app/event_closing_reminder.html",
        {
            "greeting": greeting,
            "heading": heading,
            "event_name": event_name,
            "company_name": company_name,
            "event_date": event_date,
            "location": location,
            "description": event_description,
            "message": message,
            "button_text": button_text,
            "button_link": button_link,
            "disclaimer": disclaimer,
            "base_url": base_url,
        },
    )

    # Plain text version
    plain_text = f"{greeting}\n\n{heading}\n\n"
    plain_text += f"{event_name} with {company_name}\n"
    if location:
        plain_text += f"Location: {location}\n"
    plain_text += f"Closes: {event_date}\n\n"
    if event_description:
        plain_text += f"{re.sub('<[^<]+?>', '', event_description)}\n\n"
    plain_text += f"{message}\n\n"
    if button_link:
        plain_text += f"{button_text}: {button_link}\n\n"
    if disclaimer:
        plain_text += f"⚠️ {disclaimer}\n"

    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]

    send_mail(
        subject=subject,
        message=plain_text,
        html_message=html_message,
        from_email=from_email,
        recipient_list=recipient_list,
        fail_silently=False,
    )


def send_event_reminder_email(
    email: str,
    event_name: str,
    company_name: str,
    event_type: str,
    event_start: datetime,
    event_description: str = "",
    location: str | None = "",
    button_link: str = "",
    disclaimer: str | None = "",
    hours_before: int = 24,  # 24 for tomorrow, 1 for one hour
    request: HttpRequest | None = None,
) -> None:
    """
    Send a reminder email that the event is starting soon (tomorrow or in one hour).

    Args:
        email: Recipient email address
        event_name: Name of the event
        company_name: Name of the company
        event_type: Type of event (e.g., 'Lunch', 'Company Visit', 'Student Session')
        event_start: When the event starts
        event_description: Description of the event
        location: Event location
        button_link: Link to event details
        disclaimer: Special disclaimer (e.g., for SAAB, FMV)
        hours_before: 24 for tomorrow, 1 for one hour before
        request: HttpRequest object to get the base URL (optional)
    """
    time_phrase = "tomorrow" if hours_before == 24 else "in one hour"

    subject = f"{event_type} with {company_name} is {time_phrase}"
    greeting = "Reminder!"
    heading = f"You're registered for {event_type} which is {time_phrase}"
    message = "We look forward to seeing you!"
    button_text = "View event details"

    event_date = event_start.strftime("%Y-%m-%d")
    event_time = event_start.strftime("%H:%M")

    base_url = get_base_url(request) if request else get_base_url_from_settings()
    html_message = render_to_string(
        "email_app/event_reminder.html",
        {
            "greeting": greeting,
            "heading": heading,
            "event_name": event_name,
            "company_name": company_name,
            "event_date": event_date,
            "event_time": event_time,
            "location": location,
            "description": event_description,
            "message": message,
            "button_text": button_text,
            "button_link": button_link,
            "disclaimer": disclaimer,
            "base_url": base_url,
        },
    )

    # Plain text version
    plain_text = f"{greeting}\n\n{heading}\n\n"
    plain_text += f"{event_name} with {company_name}\n"
    if location:
        plain_text += f"Location: {location}\n"
    plain_text += f"Date: {event_date}\n"
    plain_text += f"Time: {event_time}\n\n"
    if event_description:
        plain_text += f"{re.sub('<[^<]+?>', '', event_description)}\n\n"
    plain_text += f"{message}\n\n"
    if button_link:
        plain_text += f"{button_text}: {button_link}\n\n"
    if disclaimer:
        plain_text += f"⚠️ {disclaimer}\n"

    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]

    send_mail(
        subject=subject,
        message=plain_text,
        html_message=html_message,
        from_email=from_email,
        recipient_list=recipient_list,
        fail_silently=False,
    )


def send_event_selection_email(
    email: str,
    event_name: str,
    company_name: str,
    event_type: str,
    message: str,
    event_start: datetime | None,
    event_description: str = "",
    location: str | None = "",
    button_link: str = "",
    disclaimer: str | None = "",
    request: HttpRequest | None = None,
) -> None:
    """
    Send an email notifying the user they've been selected for a student session or company visit.

    Args:
        email: Recipient email address
        event_name: Name of the event
        company_name: Name of the company
        event_type: Type of event (e.g., 'Student Session', 'Company Visit')
        event_start: When the event starts
        event_description: Description of the event
        location: Event location
        button_link: Link to event details
        disclaimer: Special disclaimer (e.g., for SAAB, FMV)
        request: HttpRequest object to get the base URL (optional)
    """
    subject = f"You've been selected for {event_type} with {company_name}!"
    greeting = "Congratulations!"
    heading = f"You've been selected for {event_type}"
    button_text = "View event details"

    event_date = event_start.strftime("%Y-%m-%d") if event_start else None
    event_time = event_start.strftime("%H:%M") if event_start else None

    base_url = get_base_url(request) if request else get_base_url_from_settings()
    html_message = render_to_string(
        "email_app/event_selection.html",
        {
            "greeting": greeting,
            "heading": heading,
            "event_name": event_name,
            "company_name": company_name,
            "event_date": event_date,
            "event_time": event_time,
            "location": location,
            "description": event_description,
            "message": message,
            "button_text": button_text,
            "button_link": button_link,
            "disclaimer": disclaimer,
            "base_url": base_url,
        },
    )

    # Plain text version
    plain_text = f"{greeting}\n\n{heading}\n\n"
    plain_text += f"{event_name} with {company_name}\n"
    if location:
        plain_text += f"Location: {location}\n"
    plain_text += f"Date: {event_date}\n"
    plain_text += f"Time: {event_time}\n\n"
    if event_description:
        plain_text += f"{re.sub('<[^<]+?>', '', event_description)}\n\n"
    plain_text += f"{message}\n\n"
    if button_link:
        plain_text += f"{button_text}: {button_link}\n\n"
    if disclaimer:
        plain_text += f"⚠️ {disclaimer}\n"

    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]

    send_mail(
        subject=subject,
        message=plain_text,
        html_message=html_message,
        from_email=from_email,
        recipient_list=recipient_list,
        fail_silently=False,
    )
