from django.db import models
from django.db.models import Q, QuerySet
from django.utils import timezone

from companies.models import Company
from user_models.models import User

EVENT_TYPES: dict[str, str] = {
    "ce": "Company event",
    "lu": "Lunch",
    "ba": "Banquet"
}

class Event(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    type = models.CharField(choices=EVENT_TYPES, max_length=2)
    location = models.CharField(max_length=300)
    language = models.CharField(max_length=100, default="Swedish")

    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=False)

    start_time = models.DateTimeField(null=False)
    end_time = models.DateTimeField(null=False)

    capacity = models.IntegerField(null=False)

    attending = models.ManyToManyField(to=User)
    number_booked = models.IntegerField(null=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(number_booked__lte=models.F('capacity')),
                name='capacity_not_exceeded'
            )
        ]

    @staticmethod
    def available_filter() -> Q:
        return Q(
            start_time__gte=timezone.now(),
        )

    @classmethod
    def available_events(cls) -> QuerySet:
        return cls.objects.filter(cls.available_filter()).all()
