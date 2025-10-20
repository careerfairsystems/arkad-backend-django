import datetime
from datetime import timedelta
from functools import partial
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import UniqueConstraint
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.utils import timezone
from arkad.defaults import (
    STUDENT_SESSIONS_OPEN_UTC,
    STUDENT_SESSIONS_CLOSE_UTC,
    STUDENT_TIMESLOT_BOOKING_CLOSE_UTC,
)
from arkad.settings import APP_BASE_URL
from arkad.utils import unique_file_upload_path
from notifications.models import ScheduledCeleryTasks
from student_sessions.dynamic_fields import FieldModificationSchema
from user_models.models import User
from companies.models import Company
from django_pydantic_field import SchemaField

COMPANY_EVENT_DEFAULT_DURATION: int = 480  # 8 hours in minutes


class ApplicationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"


class SessionType(models.TextChoices):
    REGULAR = "regular", "Regular"
    COMPANY_EVENT = "company_event", "Company Event"


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
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.PENDING,
    )

    notify_timeslot_tomorrow = models.ForeignKey(
        ScheduledCeleryTasks,
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="notify_timeslot_tomorrow",
        blank=True,
    )

    notify_timeslot_in_one_hour = models.ForeignKey(
        ScheduledCeleryTasks,
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="notify_timeslot_in_one_hour",
        blank=True,
    )

    notify_timeslot_booking_closes_tomorrow = models.ForeignKey(
        ScheduledCeleryTasks,
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="notify_timeslot_booking_closes_tomorrow",
        blank=True,
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
        self.status = ApplicationStatus.ACCEPTED

        # For company events, automatically create a timeslot if it doesn't exist
        if self.student_session.session_type == SessionType.COMPANY_EVENT:
            with transaction.atomic():
                timeslot, created = (
                    StudentSessionTimeslot.objects.select_for_update().get_or_create(
                        student_session=self.student_session,
                        start_time=self.student_session.company_event_at,
                        defaults={
                            "duration": COMPANY_EVENT_DEFAULT_DURATION,  # 8 hours in minutes
                        },
                    )
                )
                # Automatically add this application to the timeslot
                timeslot.add_selection(self)

        from notifications.models import Notification  # Avoid circular import

        link = f"{APP_BASE_URL}/sessions/book/{self.student_session.company.id if self.student_session.company else ''}"
        Notification.objects.create(
            target_user=self.user,
            title=f"Your application to {self.student_session.company.name} has been accepted",
            body=f"Congratulations! Your application to {self.student_session.company.name} has been accepted. Enter the app to see more information",
            greeting=f"Hi {self.user.first_name},",
            heading="Application Accepted",
            button_text="View Session",
            button_link=link,
            fcm_link=link,
            note="We look forward to seeing you there!",
            email_sent=True,
            fcm_sent=True,
        )
        self.save()

    def deny(self) -> None:
        self.status = ApplicationStatus.REJECTED

        self.user.email_user(
            f"Your application to {self.student_session.company.name} has been rejected",
            "We regret to inform you that your application has been rejected.\n",
        )
        self.save()

    def is_accepted(self) -> bool:
        return self.status == ApplicationStatus.ACCEPTED

    def is_rejected(self) -> bool:
        return self.status == ApplicationStatus.REJECTED

    def is_pending(self) -> bool:
        return self.status == ApplicationStatus.PENDING

    @staticmethod
    def get_valid_statuses() -> list[str]:
        return [choice[0] for choice in ApplicationStatus.choices]

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        """Override delete to ensure CV file is removed from filesystem"""
        if self.cv:
            self.cv.delete(save=False)
        return super().delete(*args, **kwargs)

    def schedule_notifications(
        self,
        start_time: datetime.datetime,
        unbook_closes_at: datetime.datetime,
        timeslot_id: int,
    ) -> None:
        # You have registered for YYY with XXX is tomorrow/ in one hour
        assert self.is_accepted(), (
            "Can only schedule notifications for accepted applications"
        )
        from notifications import tasks

        self.remove_notifications()  # Make sure to not duplicate tasks

        eta1 = start_time - timedelta(hours=24)
        if eta1 > timezone.now():
            self.notify_timeslot_tomorrow = ScheduledCeleryTasks.schedule_task(
                task_function=tasks.notify_student_session_tomorrow,
                eta=eta1,
                arguments=[self.user.id, self.student_session.id, timeslot_id],
            )

        eta2 = start_time - timedelta(hours=1)
        if eta2 > timezone.now():
            self.notify_timeslot_in_one_hour = ScheduledCeleryTasks.schedule_task(
                task_function=tasks.notify_student_session_one_hour,
                eta=eta2,
                arguments=[self.user.id, self.student_session.id, timeslot_id],
            )
        eta3 = unbook_closes_at - timedelta(days=1)
        if eta3 > timezone.now():
            self.notify_timeslot_booking_closes_tomorrow = ScheduledCeleryTasks.schedule_task(
                task_function=tasks.notify_student_session_timeslot_booking_freezes_tomorrow,
                eta=eta3,
                arguments=[timeslot_id, self.id],
            )
        self.save()

    def remove_notifications(self) -> None:
        if self.notify_timeslot_tomorrow:
            self.notify_timeslot_tomorrow.revoke()
            self.notify_timeslot_tomorrow = None
        if self.notify_timeslot_in_one_hour:
            self.notify_timeslot_in_one_hour.revoke()
            self.notify_timeslot_in_one_hour = None
        if self.notify_timeslot_booking_closes_tomorrow:
            self.notify_timeslot_booking_closes_tomorrow.revoke()
            self.notify_timeslot_booking_closes_tomorrow = None
        self.save()


class StudentSessionTimeslot(models.Model):
    selected_applications = models.ManyToManyField(
        StudentSessionApplication,
        related_name="selected_timeslots",
        blank=True,
        help_text="Selected applications for this timeslot - supports multiple for company events",
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

    booking_closes_at = models.DateTimeField(
        default=STUDENT_TIMESLOT_BOOKING_CLOSE_UTC,
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

    def is_available_for_application(self) -> bool:
        """Check if this timeslot is available for booking."""
        session_type = self.student_session.session_type

        if session_type == SessionType.COMPANY_EVENT:
            # Company events allow multiple selections
            return True
        else:  # regular
            # Regular sessions only allow one selection
            return self.selected_applications.count() == 0

    def add_selection(self, application: StudentSessionApplication) -> None:
        """Add an application selection to this timeslot."""
        self.selected_applications.add(application)

    def remove_selection(self, application: StudentSessionApplication) -> None:
        """Remove an application selection from this timeslot."""
        self.selected_applications.remove(application)

    def get_selected_application(self) -> StudentSessionApplication | None:
        """Get the single selected application for regular sessions."""
        return self.selected_applications.first()

    def save(self, *args, **kwargs) -> None:  # type: ignore
        # Override the save method of the model
        # Schedule a notification task
        if self.pk is not None:
            if self.selected_applications.exists():
                self._remove_notifications()
                self._schedule_notifications()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]:  # type: ignore
        self._remove_notifications()
        return super().delete(*args, **kwargs)

    def _schedule_notifications(self) -> None:
        # You have registered for YYY with XXX is tomorrow/ in one hour
        for application in self.selected_applications.all():
            application.schedule_notifications(
                self.start_time,
                unbook_closes_at=self.booking_closes_at,
                timeslot_id=self.id,
            )

    def _remove_notifications(self) -> None:
        for application in self.selected_applications.all():
            application.remove_notifications()


class StudentSession(models.Model):
    company = models.ForeignKey(  # Must be a foreign key to Company, as a company may have a student session and a company event
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
    location = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Location of the student session, shown to students when applying",
    )
    disclaimer = models.TextField(
        null=True,
        blank=True,
        help_text="Disclaimer shown to students when applying (example SAAB requiring ONLY swedish citizens)",
    )
    session_type = models.CharField(
        max_length=20,
        choices=SessionType.choices,
        default=SessionType.REGULAR,
        help_text="The type of the student session",
    )

    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    company_event_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="The date and time of the company event, if applicable",
    )
    name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Name for the session, if not used the company name is shown",
    )

    notify_registration_open = models.ForeignKey(
        ScheduledCeleryTasks,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
        related_name="student_session_notify_registration_open",
    )

    def __str__(self) -> str:
        return self.name or self.company.name

    def clean(self) -> None:
        """
        Custom validation to ensure company_event_at is set if the session_type is COMPANY_EVENT.
        """
        # Check for the specific condition:
        if (
            self.session_type == SessionType.COMPANY_EVENT
            and self.company_event_at is None
        ):
            # Raise a ValidationError if the condition is not met
            raise ValidationError(
                {
                    "company_event_at": (
                        "A COMPANY_EVENT type session must have a defined company event start time."
                    )
                }
            )
        return super().clean()

    def schedule_notifications(self) -> None:
        from notifications import tasks

        if self.notify_registration_open:
            # Revoke existing task if it exists
            self.notify_registration_open.revoke()

        if self.booking_open_time and self.booking_open_time > timezone.now():
            # Check that booking_open_time is in the future
            self.notify_registration_open = ScheduledCeleryTasks.schedule_task(
                task_function=tasks.notify_student_session_registration_open,
                eta=self.booking_open_time,
                arguments=[self.id],
            )

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Calls full clean before saving to ensure constraints are checked.
        """
        self.full_clean()
        saved = super().save(*args, **kwargs)
        self.schedule_notifications()  # After save so id is not None
        return saved

    def revoke_and_reschedule_tasks(self) -> None:
        # Remove and reschedule notifications for the session itself
        self.schedule_notifications()  # This already revokes and reschedules
        # For each timeslot, for each selected application, remove and reschedule notifications if timeslot is in the future
        for timeslot in self.timeslots.all():
            for application in timeslot.selected_applications.all():
                application.remove_notifications()
                if timeslot.start_time > timezone.now() and application.is_accepted():
                    application.schedule_notifications(
                        timeslot.start_time,
                        unbook_closes_at=timeslot.booking_closes_at,
                        timeslot_id=timeslot.id,
                    )

                setattr(application, "_signal_receivers_disabled", True)
                application.save()
            setattr(timeslot, "_signal_receivers_disabled", True)
            timeslot.save()
        setattr(self, "_signal_receivers_disabled", True)
        self.save()


@receiver(m2m_changed, sender=StudentSessionTimeslot.selected_applications.through)
def validate_single_selection(
    sender: Any, instance: StudentSessionTimeslot, action: str, **kwargs: Any
) -> None:
    if action in ("post_add", "post_remove", "post_clear"):
        if (
            instance.student_session.session_type == SessionType.REGULAR
            and instance.selected_applications.count() > 1
        ):
            raise ValidationError(
                "Regular sessions can only have one selected application"
            )
