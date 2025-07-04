from functools import partial

from django.db import models
from django.db.models import Q, UniqueConstraint
from django.utils import timezone

from arkad.utils import unique_file_upload_path
from user_models.models import User
from companies.models import Company


class StudentSessionApplication(models.Model):
    student_session = models.ForeignKey(
        "StudentSession", on_delete=models.CASCADE, null=False
    )

    timestamp = models.DateTimeField(default=timezone.now)
    motivation_text = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cv = models.FileField("Users cv",
                          upload_to=partial(unique_file_upload_path, "application/cv"),
                          null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=[
            ("pending", "Pending"),
            ("accepted", "Accepted"),
            ("rejected", "Rejected"),
        ],
        default="pending",
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["student_session", "user"],
                name="unique_student_session_motivation",
            )
        ]

    def __str__(self) -> str:
        return f"Application by {self.user} to {self.student_session.company.name}"

    def accept(self) -> None:
        self.status = "accepted"

        self.user.email_user(
            "Application accepted",
            "Your application has been accepted, enter the app and select a timeslot\n "
            "They may run out at any time.\n",
        )
        self.save()

    def deny(self) -> None:
        self.status = "rejected"

        self.user.email_user(
            f"Your application to {self.student_session.company.name} has been rejected",
            "We regret to inform you that your application has been rejected.\n",
        )
        self.save()

    def is_accepted(self) -> bool:
        return self.status == "accepted"

    def is_rejected(self) -> bool:
        return self.status == "rejected"

    def is_pending(self) -> bool:
        return self.status == "pending"


class StudentSessionTimeslot(models.Model):
    selected = models.OneToOneField(
        StudentSessionApplication, on_delete=models.SET_NULL, null=True, blank=True
    )
    student_session = models.ForeignKey(
        "StudentSession",
        on_delete=models.CASCADE,
        null=False,
        related_name="timeslots",
    )

    start_time = models.DateTimeField(null=False)
    duration = models.IntegerField(
        default=30, help_text="Duration of the student session in minutes"
    )

    time_booked = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["student_session", "start_time"],
                name="unique_student_session_timeslot",
            )
        ]

    def __str__(self) -> str:
        return f"Timeslot {self.start_time} - {self.duration} minutes"


class StudentSession(models.Model):
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        null=False,
        related_name="company_representative",
    )
    booking_close_time = models.DateTimeField(null=True, blank=True)

    @staticmethod
    def available_filter() -> Q:
        return Q(
            start_time__gte=timezone.now(),
            booking_close_time__gte=timezone.now(),
        )

    def __str__(self) -> str:
        return f"ID {self.id}: {self.company.name}"
