import logging
from typing import Any

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from firebase_admin.messaging import UnregisteredError  # type: ignore[import-untyped]

from email_app.emails import send_generic_information_email
from notifications.fcm_helper import fcm


class Notification(models.Model):
    target_user = models.ForeignKey(
        "user_models.User",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    notification_topic = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="FCM Topic"
    )  # FCM topic
    title = models.CharField(
        max_length=255, verbose_name="Title for notification or subject for email"
    )  # Subject if email
    body = models.TextField(
        verbose_name="Body of notification or email body if email body not set"
    )  # Message if email
    fcm_link = models.URLField(
        null=True, blank=True, help_text="Link opened when notification is clicked"
    )  # Optional link opened when notification is clicked

    email_body = models.TextField(
        null=True, blank=True, verbose_name="Custom email body"
    )  # Optional custom email body, if not set body is used

    greeting = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Greeting used in email"
    )  # Optional greeting for email
    heading = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Heading used in email"
    )  # Optional heading for email
    button_text = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Button text used in email"
    )  # Optional button text for email
    button_link = models.URLField(
        null=True, blank=True, help_text="Button link used in email"
    )  # Optional button link for
    note = models.TextField(
        null=True, blank=True, help_text="Note text used in email"
    )  # Optional note for email

    email_sent = models.BooleanField(default=False)
    fcm_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)

    auto_send_on_create = models.BooleanField(
        "Should this be sent out automatically when created?", default=True
    )

    def __str__(self) -> str:
        return f"Notification to {self.target_user} - {self.notification_topic} at {self.sent_at}"

    class Meta:
        # Set constraint so not both topic and user can be set, nor both can be null
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(target_user__isnull=False, notification_topic__isnull=True)
                    | models.Q(
                        target_user__isnull=True, notification_topic__isnull=False
                    )
                ),
                name="either_user_or_topic_not_both",
            )
        ]


# Automatically send out notifications when a Notification is created
@receiver(pre_save, sender=Notification)
def send_notification(sender: Any, instance: Notification, **kwargs: Any) -> None:
    created = instance.pk is None  # Check if the instance is being created
    if created and instance.auto_send_on_create:
        sent_fcm: bool = False
        sent_email: bool = False
        try:
            if instance.target_user and instance.fcm_sent:
                # Send FCM notification to the user
                sent_fcm = fcm.send_to_user(
                    user=instance.target_user,
                    title=instance.title,
                    body=instance.body,
                    link=instance.fcm_link,
                )
            elif instance.notification_topic and instance.fcm_sent:
                # Send FCM notification to the topic
                sent_fcm = fcm.send_to_topic(
                    topic=instance.notification_topic,
                    title=instance.title,
                    body=instance.body,
                    link=instance.fcm_link,
                )
        except UnregisteredError as e:
            # The FCM token is no longer valid, clear it from the user
            if instance.target_user:
                instance.target_user.fcm_token = None
                instance.target_user.save(update_fields=["fcm_token"])
            sent_fcm = False
            logging.error(f"UnregisteredError: {e}")

        if instance.target_user and instance.email_sent:
            send_generic_information_email(
                email=instance.target_user.email,
                subject=instance.title,
                name=instance.target_user.first_name,
                greeting=instance.greeting or "Hello!",
                heading=instance.heading or instance.title,
                message=instance.email_body or instance.body or "",
                button_text=instance.button_text or "",
                button_link=instance.button_link or "",
                note=instance.note or "Best regards, Arkad IT Team",
            )
            sent_email = True
        instance.fcm_sent = sent_fcm
        instance.email_sent = sent_email
