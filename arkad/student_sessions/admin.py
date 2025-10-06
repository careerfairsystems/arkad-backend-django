from typing import Any

from django.contrib import admin
from django.http import HttpRequest
from import_export.admin import ImportExportModelAdmin

from .models import StudentSession, StudentSessionApplication, StudentSessionTimeslot
from .import_export_resources import StudentSessionApplicationResource


@admin.register(StudentSessionApplication)
class StudentSessionApplicationAdmin(ImportExportModelAdmin):  # type: ignore[type-arg]
    resource_classes = [StudentSessionApplicationResource]

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
    list_filter = ("student_session__company", "status")

    # Make some fields read-only in the admin detail view for safety
    readonly_fields = ("timestamp",)

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


@admin.register(StudentSessionTimeslot)
class StudentSessionTimeslotAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("student_session", "start_time", "duration", "get_selected_count")
    list_filter = ("student_session__company",)

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
