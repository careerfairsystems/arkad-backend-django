import uuid
from datetime import timedelta, datetime

from celery.result import AsyncResult  # type: ignore[import-untyped]
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, UniqueConstraint, CheckConstraint, QuerySet
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

    notify_event_tmrw_id = models.CharField(default=None, null=True, blank=True)
    notify_event_one_hour_id = models.CharField(default=None, null=True, blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(name="one_ticket_per_user_event", fields=("user", "event"))
        ]

    def __str__(self) -> str:
        return f"{self.user}'s ticket to {self.event}"

    def status(self) -> EventUserStatus:
        return EventUserStatus.TICKET_USED if self.used else EventUserStatus.BOOKED

    def save(self, *args, **kwargs) -> None: # type: ignore
        # Override the save method of the model
        # Schedule a notification task
        self._remove_notifications()
        self._schedule_notifications()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]: # type: ignore
        self._remove_notifications()
        return super().delete(*args, **kwargs)

    def _schedule_notifications(self) -> None:
        from notifications import tasks
        #(Du har anmält dig till) YYY (som är) med XXX är imorgon
        task_notify_event_tmrw = tasks.notify_event_tmrw.apply_async(
            args=[self.user.id, self.event.id],
            eta=self.event.start_time - timedelta(hours=24)
        )
        self.notify_event_tmrw_id = task_notify_event_tmrw.id

        #(Du har anmält dig till) YYY (som är) med XXX är om en timme
        task_notify_event_one_hour = tasks.notify_event_one_hour.apply_async(
            args=[self.user.id, self.event.id],
            eta=self.event.start_time - timedelta(hours=1)
        )
        self.notify_event_one_hour_id = task_notify_event_one_hour.id
    
    def _remove_notifications(self) -> None:
        if self.notify_event_tmrw_id:
            AsyncResult(self.notify_event_tmrw_id).revoke()
            self.notify_event_tmrw_id = None
 
        if self.notify_event_tmrw_id:
            AsyncResult(self.notify_event_tmrw_id).revoke()
            self.notify_event_one_day_id = None


class Event(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(default="")

    type = models.CharField(choices=EVENT_TYPES, max_length=2)  # type: ignore[arg-type]
    location = models.CharField(max_length=300, null=True)
    language = models.CharField(max_length=100, default="Swedish")

    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=False)

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
        default=0, null=False
    )  # Counter for booked tickets
    capacity = models.IntegerField(null=False)

    notify_registration_open_id = models.CharField(default=None, null=True, blank=True)

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

    @staticmethod
    def available_filter() -> Q:
        return Q(
            start_time__gte=timezone.now(),
        )

    @classmethod
    def available_events(cls) -> QuerySet["Event"]:
        return cls.objects.filter(cls.available_filter()).all()

    def save(self, *args, **kwargs) -> None: # type: ignore
        # Override the save method of the model
        # Schedule a notification task
        self._remove_notifications()
        self._schedule_notifications()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]: # type: ignore
        self._remove_notifications()
        return super().delete(*args, **kwargs)

    def _schedule_notifications(self) -> None:
        from notifications import tasks
        #Anmälan för företagsbesök/lunchföreläsning med XXX har öppnat
        task_notify_registration_open = tasks.notify_event_reg_open.apply_async(
            args=[self.id],
            eta=self.release_time
        )
        self.notify_registration_open_id = task_notify_registration_open.id

    def _remove_notifications(self) -> None:
        if self.notify_registration_open_id:
            AsyncResult(self.notify_registration_open_id).revoke()
            self.notify_registration_open_id = None

