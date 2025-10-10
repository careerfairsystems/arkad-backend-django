import uuid
from datetime import timedelta, datetime
from typing import Any, Type

from celery.result import AsyncResult  # type: ignore[import-untyped]
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, CheckConstraint
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from arkad.defaults import DEFAULT_VISIBLE_TIME_EVENT, DEFAULT_RELEASE_TIME_EVENT
from companies.models import Company
from event_booking.schemas import EventUserStatus
from user_models.models import User

EVENT_TYPES: dict[str, str] = {"ce": "Company event", "lu": "Lunch", "ba": "Banquet"}


class Ticket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey("Event", on_delete=models.CASCADE, related_name="tickets")
    used = models.BooleanField(default=False)

    task_id_notify_event_tomorrow = models.CharField(
        default=None, null=True, blank=True, editable=False
    )
    task_id_notify_event_in_one_hour = models.CharField(
        default=None, null=True, blank=True, editable=False
    )

    def __str__(self) -> str:
        return f"{self.user}'s ticket to {self.event}"

    def status(self) -> EventUserStatus:
        return EventUserStatus.TICKET_USED if self.used else EventUserStatus.BOOKED

    def schedule_notifications(self, start_time: datetime) -> None:
        """Schedule notifications for this ticket."""
        from notifications import tasks

        # (Du har anmält dig till) YYY (som är) med XXX är imorgon
        task_notify_event_tmrw = tasks.notify_event_tomorrow.apply_async(
            args=[self.user.id, self.event.id],
            eta=start_time - timedelta(hours=24),
        )
        self.task_id_notify_event_tomorrow = task_notify_event_tmrw.id

        # (Du har anmält dig till) YYY (som är) med XXX är om en timme
        task_notify_event_one_hour = tasks.notify_event_one_hour.apply_async(
            args=[self.user.id, self.event.id],
            eta=start_time - timedelta(hours=1),
        )
        self.task_id_notify_event_in_one_hour = task_notify_event_one_hour.id

    def remove_notifications(self) -> None:
        """Remove scheduled notifications for this ticket."""
        if self.task_id_notify_event_tomorrow:
            AsyncResult(self.task_id_notify_event_tomorrow).revoke()
            self.task_id_notify_event_tomorrow = None

        if self.task_id_notify_event_in_one_hour:
            AsyncResult(self.task_id_notify_event_in_one_hour).revoke()
            self.task_id_notify_event_in_one_hour = None

    def save(self, *args: Any, **kwargs: Any) -> None:
        # On update, remove old notifications
        if not self._state.adding:
            old_instance = Ticket.objects.get(pk=self.pk)
            old_instance.remove_notifications()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]:  # type: ignore
        self.remove_notifications()
        return super().delete(*args, **kwargs)


@receiver(post_save, sender=Ticket)
def schedule_ticket_notifications(
    sender: Type[Ticket], instance: Ticket, created: bool, **kwargs: Any
) -> None:
    if created:
        instance.schedule_notifications(instance.event.start_time)
        instance.save(
            update_fields=[
                "task_id_notify_event_tomorrow",
                "task_id_notify_event_in_one_hour",
            ]
        )


class Event(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(default="")

    type = models.CharField(choices=EVENT_TYPES, max_length=2)  # type: ignore[arg-type]
    location = models.CharField(max_length=300, null=True)
    language = models.CharField(max_length=100, default="Swedish")

    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True)

    visible_time = models.DateTimeField(
        null=False,
        default=DEFAULT_VISIBLE_TIME_EVENT,
        verbose_name="The time the event becomes visible",
    )
    release_time = models.DateTimeField(
        null=True,
        default=DEFAULT_RELEASE_TIME_EVENT,
        verbose_name="The time the event is released",
    )

    start_time = models.DateTimeField(null=False)
    end_time = models.DateTimeField(null=False)

    number_booked = models.IntegerField(
        default=0, null=False, editable=False
    )  # Counter for booked tickets
    capacity = models.IntegerField(null=False)

    task_id_notify_registration_opening = models.CharField(
        default=None, null=True, blank=True, editable=False
    )

    class Meta:
        constraints = [
            CheckConstraint(
                check=Q(number_booked__lte=models.F("capacity")),
                name="capacity_not_exceeded",
            )
        ]

    def clean(self) -> None:
        if self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time.")
        return super().clean()

    @staticmethod
    def booking_change_deadline_delta() -> timedelta:
        """Returns the timedelta before the event start time when unbooking is no longer allowed."""
        return timedelta(weeks=1)

    @property
    def booking_freezes_at(self) -> datetime:
        """Returns the time when booking/unbooking is no longer allowed."""
        return self.start_time - self.booking_change_deadline_delta()

    def booking_change_allowed(self) -> bool:
        """Unbooking is only allowed if there is longer than 1 week until the event starts."""
        return timezone.now() < self.booking_freezes_at

    def __str__(self) -> str:
        return f"{self.name}'s event {self.start_time} to {self.end_time}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        # On update, remove old notifications
        if not self._state.adding:
            old_instance = Event.objects.get(pk=self.pk)
            old_instance._remove_notifications()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]:  # type: ignore
        self._remove_notifications()
        return super().delete(*args, **kwargs)

    def _schedule_notifications(self) -> None:
        from notifications import tasks

        # Anmälan för företagsbesök/lunchföreläsning med XXX har öppnat
        task_notify_registration_open = (
            tasks.notify_event_registration_open.apply_async(
                args=[self.id], eta=self.release_time
            )
        )
        self.task_id_notify_registration_opening = task_notify_registration_open.id

    def _remove_notifications(self) -> None:
        if self.task_id_notify_registration_opening:
            AsyncResult(self.task_id_notify_registration_opening).revoke()
            self.task_id_notify_registration_opening = None

    def verify_user_has_ticket(self, user_id: int) -> bool:
        return self.tickets.filter(user_id=user_id, used=False).exists()

    def get_event_type_display(self) -> str:
        if self.type == "ce":
            return "Company visit"
        elif self.type == "lu":
            return "Lunch lecture"
        elif self.type == "ba":
            return "Banquet"
        else:
            return "Event"


@receiver(post_save, sender=Event)
def schedule_event_notifications(
    sender: Type[Event], instance: Event, created: bool, **kwargs: Any
) -> None:
    if created:
        instance._schedule_notifications()
        instance.save(update_fields=["task_id_notify_registration_opening"])
