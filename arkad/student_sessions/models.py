from django.db import models
from django.db.models import Q, QuerySet, UniqueConstraint
from django.utils import timezone

from user_models.models import User
from companies.models import Company


class CompanyStudentSessionMotivation(models.Model):
    motivation_text = models.TextField(null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["company", "user"], name="unique_student_session_motivation"
            )
        ]


class StudentSessionApplication(models.Model):
    motivation = models.ForeignKey(
        CompanyStudentSessionMotivation, on_delete=models.CASCADE
    )


class StudentSession(models.Model):
    interviewee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="interviewee",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=False,
        related_name="company_representative",
    )

    start_time = models.DateTimeField(null=False)
    duration = models.IntegerField(
        default=30, help_text="Duration of the student session in minutes"
    )

    booking_close_time = models.DateTimeField(null=True, blank=True)

    applications = models.ManyToManyField(to=StudentSessionApplication)

    class Meta:
        constraints = [
            UniqueConstraint(
                name="No duplicated start time", fields=("start_time", "company")
            ),
            UniqueConstraint(
                name="A single user may only book one session per company",
                fields=("interviewee", "company"),
            ),
        ]

    @property
    def available(self) -> bool:
        return self.interviewee is None

    @staticmethod
    def available_filter() -> Q:
        return Q(
            interviewee=None,
            start_time__gte=timezone.now(),
            booking_close_time__gte=timezone.now(),
        )

    @classmethod
    def available_sessions(cls) -> QuerySet["StudentSession"]:
        return cls.objects.filter(cls.available_filter()).all()

    def __str__(self) -> str:
        return f"{self.company.name}:  {self.start_time}"
