from datetime import timedelta
from functools import partial

from django.db import models
from django.db.models import UniqueConstraint
from django.utils import timezone
from celery.result import AsyncResult  # type: ignore[import-untyped]
from arkad.defaults import (
    STUDENT_SESSIONS_OPEN_UTC,
    STUDENT_SESSIONS_CLOSE_UTC,
    STUDENT_TIMESLOT_BOOKING_CLOSE_UTC,
)
from arkad.utils import unique_file_upload_path
from student_sessions.dynamic_fields import FieldModificationSchema
from user_models.models import User
from companies.models import Company
from django_pydantic_field import SchemaField


class StudentSessionApplication(models.Model):
    student_session = models.ForeignKey(
        "StudentSession", on_delete=models.CASCADE, null=False
    )

    timestamp = models.DateTimeField(default=timezone.now)
    motivation_text = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cv = models.FileField(
        "Users cv",
        upload_to=partial(unique_file_upload_path, "application/cv"),
        null=True,
        blank=True,
    )
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

    notify_tmrw_id = models.CharField(default=None, null=True)
    notify_one_hour_id = models.CharField(default=None, null=True)
    booking_closes_at = models.DateTimeField(
        default=STUDENT_TIMESLOT_BOOKING_CLOSE_UTC,
        null=True,
        help_text="The time the timeslot is no longer bookable",
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["student_session", "start_time"],
                name="unique_student_session_timeslot",
            )
        ]

    def __str__(self) -> str:
        return f"Timeslot {self.start_time} - {self.duration} minutes"

    def save(self, *args, **kwargs) -> None: # type: ignore
        # Override the save method of the model
        # Schedule a notification task
        if self.selected:
            self._remove_notifications()
            self._schedule_notifications()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]: # type: ignore
        self._remove_notifications()
        return super().delete(*args, **kwargs)

    def _schedule_notifications(self) -> None:
        from notifications import tasks
        #(Du har anmält dig till) YYY (som är) med XXX är imorgon
        if self.selected is not None:
            task_notify_tmrw = tasks.notify_event_tmrw.apply_async(
                args=[self.selected.user.id, self.student_session.id],
                eta=self.start_time - timedelta(hours=24)
            )
            self.notify_tmrw_id = task_notify_tmrw.id

            #(Du har anmält dig till) YYY (som är) med XXX är om en timme
            task_notify_one_hour = tasks.notify_event_one_hour.apply_async(
                args=[self.selected.user.id, self.student_session.id],
                eta=self.start_time - timedelta(hours=1)
            )
            self.notify_one_hour_id = task_notify_one_hour.id
    
    def _remove_notifications(self) -> None:
        if self.notify_tmrw_id:
            AsyncResult(self.notify_tmrw_id).revoke()
            self.notify_tmrw_id = None
 
        if self.notify_tmrw_id:
            AsyncResult(self.notify_tmrw_id).revoke()
            self.notify_one_day_id = None


class StudentSession(models.Model):
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        null=False,
        related_name="company_representative",
    )
    booking_open_time = models.DateTimeField(
        default=STUDENT_SESSIONS_OPEN_UTC,
        verbose_name="The time the student session is released/bookable",
    )

    booking_close_time = models.DateTimeField(
        default=STUDENT_SESSIONS_CLOSE_UTC,
        verbose_name="The time the student session is no longer bookable",
    )
    field_modifications: list[FieldModificationSchema] = SchemaField(
        schema=list[FieldModificationSchema],
        default=FieldModificationSchema.student_session_modifications_default,
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Description of the student session, shown to students when applying",
    )
    disclaimer = models.TextField(
        null=True,
        blank=True,
        help_text="Disclaimer shown to students when applying (example SAAB requiring ONLY swedish citizens)",
    )

    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self) -> str:
        return f"ID {self.id}: {self.company.name}"

