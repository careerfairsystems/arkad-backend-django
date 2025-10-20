import datetime
import logging
from typing import Any, cast

from celery import Task
from celery.result import AsyncResult
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


class ScheduledCeleryTasks(models.Model):
    task_name = models.CharField(max_length=255)
    task_arguments = models.JSONField(default=list)
    task_id = models.CharField(editable=False, unique=True)

    eta = models.DateTimeField(null=False, blank=False)
    revoked = models.BooleanField(default=False)

    status = models.CharField(max_length=255, null=True, blank=True, editable=False, default="PENDING",
                              verbose_name="Status, must be manually refreshed")
    result = models.TextField(null=True, blank=True, editable=False)
    error = models.TextField(null=True, blank=True, editable=False)

    def __str__(self) -> str:
        if not self.revoked:
            return f"Scheduled Task: {self.task_name} at {self.eta}"
        return f"Revoked Task: {self.task_name} at {self.eta}"

    @classmethod
    def schedule_task(cls, task_function: Task, eta: datetime.datetime, arguments: list[Any]) -> "ScheduledCeleryTasks":
        """
        Schedule a Celery task to be executed at a specific time (eta) with given arguments.
        Returns the ScheduledCeleryTasks instance representing the scheduled task.
        """
        scheduled_task = cls.objects.create(
            task_name=task_function.name,
            task_arguments=arguments,
            eta=eta,
            task_id=task_function.apply_async(args=arguments, eta=eta).id
        )
        logging.info(f"Scheduled task {scheduled_task.task_name} with ID {scheduled_task.task_id} at {scheduled_task.eta}")
        return scheduled_task

    @property
    def fetch_status(self) -> str:
        """
        Returns the current Celery task status.
        Does NOT depend on stored DB state, gets live state from Celery backend.
        """
        result = AsyncResult(self.task_id)
        return str(result.status)

    @property
    def fetch_result(self) -> Any:
        """
        Get the return value of the Celery task if it finished successfully.
        """
        result = AsyncResult(self.task_id)
        if result.successful():
            return result.result
        return None

    @property
    def fetch_error(self) -> Any:
        """
        Get error traceback if task failed.
        """
        result = AsyncResult(self.task_id)
        if result.failed():
            return str(result.result)  # exception message
        return None

    @classmethod
    def revoke_task_by_id(cls, task_id: str) -> None:
        """
        Revoke a scheduled Celery task.
        """
        task: "ScheduledCeleryTasks" = cls.objects.get(task_id=task_id)
        return task.revoke()

    def revoke(self) -> None:
        """
        Revoke this scheduled Celery task.
        """
        if not self.revoked:
            AsyncResult(str(self.task_id)).revoke()
            self.revoked = True
            self.save(update_fields=["revoked"])
        else:
            logging.warning(f"Task {self.task_id} already revoked.")

    def update_status(self):
        self.status = str(self.fetch_status)
        self.error = str(self.fetch_error)
        self.result = str(self.fetch_result)
        self.save()

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
