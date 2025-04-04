import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, QuerySet, UniqueConstraint, CheckConstraint
from django.utils import timezone

from companies.models import Company
from user_models.models import User

EVENT_TYPES: dict[str, str] = {"ce": "Company event", "lu": "Lunch", "ba": "Banquet"}


class Ticket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey("Event", on_delete=models.CASCADE, related_name="tickets")
    used = models.BooleanField(default=False)

    class Meta:
        constraints = [
            UniqueConstraint(name="one_ticket_per_user_event", fields=("user", "event"))
        ]

    def __str__(self) -> str:
        return f"{self.user}'s ticket to {self.event}"


class Event(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(default="")

    type = models.CharField(choices=EVENT_TYPES, max_length=2)  # type: ignore[arg-type]
    location = models.CharField(max_length=300, null=True)
    language = models.CharField(max_length=100, default="Swedish")

    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=False)

    start_time = models.DateTimeField(null=False)
    end_time = models.DateTimeField(null=False)

    number_booked = models.IntegerField(
        default=0, null=False
    )  # Counter for booked tickets
    capacity = models.IntegerField(null=False)

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
