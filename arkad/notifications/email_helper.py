import logging
from datetime import datetime

from django.utils import timezone

from arkad.settings import make_local_time
from email_app.emails import (
    send_event_reminder_email,
    send_event_closing_reminder_email,
    send_event_selection_email,
)
from notifications.models import Notification
from user_models.models import User

logger = logging.getLogger(__name__)


class EmailHelper:
    """
    Helper class for sending emails and logging them in NotificationLog.
    This wraps email_app.emails functions and ensures each email is logged.
    """

    @staticmethod
    def send_event_reminder(
        user: User,
        event_name: str,
        company_name: str,
        event_type: str,
        event_start: datetime,
        event_description: str = "",
        location: str | None = "",
        button_link: str = "",
        disclaimer: str | None = "",
        hours_before: int = 24,
    ) -> None:
        """
        Send an event reminder email and log it.

        Args:
            user: User to send email to
            event_name: Name of the event
            company_name: Name of the company
            event_type: Type of event (e.g., 'Lunch', 'Company Visit', 'Student Session')
            event_start: When the event starts (timezone-aware)
            event_description: Description of the event
            location: Event location
            button_link: Link to event details
            disclaimer: Special disclaimer (e.g., for SAAB, FMV)
            hours_before: 24 for tomorrow, 1 for one hour before
        """
        time_phrase = "tomorrow" if hours_before == 24 else "in one hour"
        # Convert to local timezone for display
        local_time = make_local_time(event_start)
        title = f"Reminder: {event_name} is {time_phrase}!"
        body = f"Don't forget the event at {location} {time_phrase} at {local_time.strftime('%H:%M')}!"

        try:
            send_event_reminder_email(
                email=user.email,
                event_name=event_name,
                company_name=company_name,
                event_type=event_type,
                event_start=event_start,
                event_description=event_description,
                location=location,
                button_link=button_link,
                disclaimer=disclaimer,
                hours_before=hours_before,
            )
            Notification.objects.create(
                target_user=user,
                title=title,
                body=body,
                email_sent=True,
            )
            logger.info(f"Sent event reminder email to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send event reminder email to {user.email}: {e}")
            raise

    @staticmethod
    def send_event_closing_reminder(
        user: User,
        event_name: str,
        company_name: str,
        event_type: str,
        closes_at: datetime,
        event_description: str = "",
        location: str | None = "",
        button_link: str = "",
        disclaimer: str | None = "",
    ) -> None:
        """
        Send an event closing reminder email and log it.

        Args:
            user: User to send email to
            event_name: Name of the event
            company_name: Name of the company
            event_type: Type of event
            closes_at: When registration closes (timezone-aware)
            event_description: Description of the event
            location: Event location
            button_link: Link to manage booking
            disclaimer: Special disclaimer
        """
        title = f"Reminder: Registration for {event_name} closes tomorrow!"
        body = f"Don't forget to unbook your spot for {event_name} if you can't attend!"

        try:
            send_event_closing_reminder_email(
                email=user.email,
                event_name=event_name,
                company_name=company_name,
                event_type=event_type,
                closes_at=closes_at,
                event_description=event_description,
                location=location,
                button_link=button_link,
                disclaimer=disclaimer,
            )
            Notification.objects.create(
                target_user=user,
                title=title,
                body=body,
                email_sent=True,
            )
            logger.info(f"Sent event closing reminder email to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send event closing reminder email to {user.email}: {e}")
            raise

    @staticmethod
    def send_event_selection(
        user: User,
        event_name: str,
        company_name: str,
        event_type: str,
        event_start: datetime | None,
        event_description: str = "",
        location: str | None = "",
        button_link: str = "",
        disclaimer: str | None = "",
    ) -> None:
        """
        Send an event selection (acceptance) email and log it.

        Args:
            user: User to send email to
            event_name: Name of the event
            company_name: Name of the company
            event_type: Type of event
            event_start: When the event starts (timezone-aware)
            event_description: Description of the event
            location: Event location
            button_link: Link to event details
            disclaimer: Special disclaimer
        """
        string_start_time = f" on {make_local_time(event_start).strftime('%Y-%m-%d %H:%M')}" if event_start else ""
        location_string = f" at {location}" if location else ""
        title = f"You have been accepted to a {event_type.lower()} with {company_name}!"
        body = f"Congratulations! You have been accepted to a {event_type.lower()} with {company_name}{string_start_time}{location_string}, check the app for more info."

        try:
            send_event_selection_email(
                email=user.email,
                event_name=event_name,
                company_name=company_name,
                event_type=event_type,
                message=body,
                event_start=event_start,
                event_description=event_description,
                location=location,
                button_link=button_link,
                disclaimer=disclaimer,
            )
            Notification.objects.create(
                target_user=user,
                title=title,
                body=body,
                email_sent=True,
            )
            logger.info(f"Sent event selection email to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send event selection email to {user.email}: {e}")
            raise


email_helper = EmailHelper()
