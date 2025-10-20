from typing import Any

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from import_export.admin import ImportExportModelAdmin

from .models import StudentSession, StudentSessionApplication, StudentSessionTimeslot
from .import_export_resources import (
    StudentSessionApplicationResource,
    StudentSessionAttendeeResource,
)


class StudentSessionListFilter(admin.SimpleListFilter):
    title = "Session"
    parameter_name = "student_session"

    def lookups(
        self,
        request: HttpRequest,
        model_admin: admin.ModelAdmin,  # type: ignore[type-arg]
    ) -> list[tuple[str, str]]:
        sessions = StudentSession.objects.all()
        return [(str(session.id), str(session)) for session in sessions]

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:  # type: ignore[type-arg]
        if self.value():
            return queryset.filter(student_session__id=self.value())
        return queryset


@admin.register(StudentSessionApplication)
class StudentSessionApplicationAdmin(ImportExportModelAdmin):  # type: ignore[type-arg]
    # Expose both the regular application resource (import/export) and the attendee export-only resource
    resource_classes = [
        StudentSessionApplicationResource,
        StudentSessionAttendeeResource,
    ]

    # --- Configuration for a better admin list view ---

    list_display = ("user", "get_company", "status", "timestamp")
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "student_session__company__name",
    )

    # This is key for your requirement to export applications for a specific company.
    # It adds a filter sidebar in the admin.
    list_filter = (
        "student_session__session_type",
        StudentSessionListFilter,
        "status",
        "student_session__company__name",
    )

    # Make some fields read-only in the admin detail view for safety
    readonly_fields = (
        "timestamp",
        "notify_timeslot_tomorrow",
        "notify_timeslot_in_one_hour",
        "notify_timeslot_booking_closes_tomorrow",
    )

    @admin.display(description="Company", ordering="student_session__company")
    def get_company(self, obj: StudentSessionApplication) -> str:
        return obj.student_session.company.name

    # This method passes keyword arguments to the Resource class's constructor.
    def get_export_resource_kwargs(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> dict[str, HttpRequest]:
        """
        Passes the request object to the resource.
        """
        return {"request": request}


# You can also register your other models for convenience
@admin.register(StudentSession)
class StudentSessionAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("company", "booking_open_time", "booking_close_time")
    actions = ["revoke_and_reschedule_tasks_action"]
    readonly_fields = [
        "notify_registration_open",
    ]

    def revoke_and_reschedule_tasks_action(self, request, queryset):  # type: ignore[no-untyped-def]
        for session in queryset:
            session.revoke_and_reschedule_tasks()
        self.message_user(
            request,
            f"Revoked and rescheduled tasks for {queryset.count()} student session(s).",
        )

    revoke_and_reschedule_tasks_action.short_description = (  # type: ignore[attr-defined]
        "Revoke and reschedule all scheduled tasks for selected student sessions"
    )


@admin.register(StudentSessionTimeslot)
class StudentSessionTimeslotAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("student_session", "start_time", "duration", "get_selected_count")
    list_filter = (StudentSessionListFilter,)

    @admin.display(description="Selected Applications")
    def get_selected_count(self, obj: StudentSessionTimeslot) -> str:
        """Display count of selected applications."""
        count = obj.selected_applications.count()
        if count == 0:
            return "None"
        elif count == 1:
            app: StudentSessionApplication | None = obj.selected_applications.first()
            if app is None:
                raise ValueError("Expected one selected application, found none.")
            return f"{app.user.get_full_name()}" if app else "1 application"
        else:
            return f"{count} applications"
