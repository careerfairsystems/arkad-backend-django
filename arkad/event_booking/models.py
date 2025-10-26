import uuid
from datetime import timedelta, datetime
from typing import Type, Any

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
from notifications.models import ScheduledCeleryTasks

EVENT_TYPES: dict[str, str] = {"ce": "Company event", "lu": "Lunch", "ba": "Banquet"}


class Ticket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey("Event", on_delete=models.CASCADE, related_name="tickets")
    used = models.BooleanField(default=False)

    notify_event_tomorrow = models.ForeignKey(
        ScheduledCeleryTasks,
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="notify_event_tomorrow",
        blank=True,
    )
    notify_event_in_one_hour = models.ForeignKey(
        ScheduledCeleryTasks,
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="notify_event_in_one_hour",
        blank=True,
    )
    notify_registration_closes_tomorrow = models.ForeignKey(
        ScheduledCeleryTasks,
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="notify_registration_closes_tomorrow",
        blank=True,
    )

    def __str__(self) -> str:
        return f"{self.user}'s ticket to {self.event}"

    def status(self) -> EventUserStatus:
        return EventUserStatus.TICKET_USED if self.used else EventUserStatus.BOOKED

    def schedule_notifications(self, start_time: datetime) -> None:
        """Schedule notifications for this ticket."""
        from notifications import tasks

        self.remove_notifications()  # Make sure that all tasks are removed

        # (Du har anmält dig till) YYY (som är) med XXX är imorgon
        eta1 = start_time - timedelta(hours=24)
        if eta1 > timezone.now():
            self.notify_event_tomorrow = ScheduledCeleryTasks.schedule_task(
                task_function=tasks.notify_event_tomorrow,
                eta=eta1,
                arguments=[self.uuid],
            )

        eta2 = start_time - timedelta(hours=1)
        if eta2 > timezone.now():
            # (Du har anmält dig till) YYY (som är) med XXX är om en timme
            self.notify_event_in_one_hour = ScheduledCeleryTasks.schedule_task(
                task_function=tasks.notify_event_one_hour,
                eta=eta2,
                arguments=[self.uuid],
            )
        # Anmälan för YYY med XXX stänger imorgon
        booking_freezes_at = self.event.booking_freezes_at
        eta3 = booking_freezes_at - timedelta(days=1)
        if eta3 > timezone.now():
            self.notify_registration_closes_tomorrow = (
                ScheduledCeleryTasks.schedule_task(
                    task_function=tasks.notify_event_registration_closes_tomorrow,
                    eta=eta3,
                    arguments=[self.uuid],
                )
            )

    def remove_notifications(self) -> None:
        """Remove scheduled notifications for this ticket."""
        if self.notify_event_tomorrow:
            self.notify_event_tomorrow.revoke()
            self.notify_event_tomorrow = None

        if self.notify_event_in_one_hour:
            self.notify_event_in_one_hour.revoke()
            self.notify_event_in_one_hour = None

        if self.notify_registration_closes_tomorrow:
            self.notify_registration_closes_tomorrow.revoke()
            self.notify_registration_closes_tomorrow = None

    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]:  # type: ignore
        self.remove_notifications()
        return super().delete(*args, **kwargs)


@receiver(post_save, sender=Ticket)
def schedule_ticket_notifications(
    sender: Type[Ticket], instance: Ticket, created: bool, **kwargs: Any
) -> None:
    should_be_processed: bool = getattr(instance, "_signal_receivers_disabled", False)

    if created and should_be_processed:
        instance.schedule_notifications(instance.event.start_time)
        setattr(instance, "_signal_receivers_disabled", True)
        instance.save(
            update_fields=[
                "notify_event_tomorrow",
                "notify_event_in_one_hour",
                "notify_registration_closes_tomorrow",
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

    notify_registration_opening = models.ForeignKey(
        ScheduledCeleryTasks,
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="notify_event_registration_opening",
        blank=True,
    )

    send_notifications_for_event = models.BooleanField(
        default=True,
        help_text="If false, no notifications will be sent for this event.",
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

    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]:  # type: ignore
        self.remove_notifications()
        return super().delete(*args, **kwargs)

    def schedule_notifications(self) -> None:
        from notifications import tasks

        self.remove_notifications()  # Make sure that all tasks are removed

        # Anmälan för företagsbesök/lunchföreläsning med XXX har öppnat
        if self.release_time and self.release_time > timezone.now():
            self.notify_registration_opening = ScheduledCeleryTasks.schedule_task(
                task_function=tasks.notify_event_registration_open,
                eta=self.release_time,
                arguments=[self.id],
            )

    def remove_notifications(self) -> None:
        if self.notify_registration_opening:
            self.notify_registration_opening.revoke()
            self.notify_registration_opening = None

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

    def revoke_and_reschedule_tasks(self) -> None:
        """
        Remove and reschedule notifications for the event and all related tickets if the event is in the future.
        """
        # Remove and reschedule notifications for the event itself
        self.remove_notifications()
        if self.send_notifications_for_event:
            self.schedule_notifications()
            # For each ticket, remove and reschedule notifications if the event is in the future
            for ticket in self.tickets.all():
                ticket.remove_notifications()
                if self.start_time > timezone.now():
                    ticket.schedule_notifications(self.start_time)
                setattr(ticket, "_signal_receivers_disabled", True)
                ticket.save()
            setattr(self, "_signal_receivers_disabled", True)
            self.save()


@receiver(post_save, sender=Event)
def schedule_event_notifications(
    sender: Type[Event], instance: Event, created: bool, **kwargs: Any
) -> None:
    # On update, remove old notifications
    if getattr(instance, "_signal_receivers_disabled", False):
        return
    if instance.send_notifications_for_event:
        instance.schedule_notifications()
        for ticket in instance.tickets.all():
            # Reschedule notifications for all tickets
            ticket.schedule_notifications(instance.start_time)
            setattr(ticket, "_signal_receivers_disabled", True)
            ticket.save(
                update_fields=[
                    "notify_event_tomorrow",
                    "notify_event_in_one_hour",
                    "notify_registration_closes_tomorrow",
                ]
            )
        # Save but do not trigger the signal again
        # Ugly fix
        setattr(instance, "_signal_receivers_disabled", True)
        instance.save(
            update_fields=[
                "notify_registration_opening",
            ]
        )
