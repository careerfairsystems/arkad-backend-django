# mypy: disable-error-code="no-untyped-def"
from typing import Any

from django.contrib import admin, messages
from django.http import HttpRequest
from django.utils.html import format_html

from arkad.settings import DEBUG
from notifications.models import Notification, ScheduledCeleryTasks


# Create a custom admin class for NotificationLog,
# No one should have change permission but create is granted to superusers
# Created notification logs are sent out automatically via FCM and/or email


@admin.register(Notification)
class NotificationLogAdmin(admin.ModelAdmin):  # type: ignore
    list_display = (
        "target_user",
        "notification_topic",
        "title",
        "email_sent",
        "fcm_sent",
        "sent_at",
    )
    list_filter = ("email_sent", "fcm_sent", "sent_at")
    search_fields = ("target_user__username", "title", "body")

    def has_add_permission(self, request: HttpRequest) -> bool:
        # Only superusers can add notification logs
        return request.user.is_superuser

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        # No one can change notification logs
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        # Only possible to delete in DEBUG mode
        return DEBUG


@admin.action(description="Fetch live status and update selected tasks")
def refetch_status_action(modeladmin, request, queryset):
    """Refetches the live status and updates the database record for selected tasks."""
    updated_count = 0
    for task in queryset:
        try:
            task.update_status()  # This calls the model method to fetch and save
            updated_count += 1
        except Exception as e:
            modeladmin.message_user(
                request,
                f"Error updating task {task.task_id}: {e}",
                level=messages.ERROR,
            )

    modeladmin.message_user(
        request, f"Successfully updated status for {updated_count} scheduled task(s)."
    )


@admin.action(description="Revoke selected pending tasks")
def revoke_tasks_action(modeladmin, request, queryset):
    """Revokes the selected Celery tasks."""
    revoked_count = 0
    # Filter to only tasks that haven't been revoked yet
    pending_tasks = queryset.filter(revoked=False)

    for task in pending_tasks:
        try:
            task.revoke()  # This calls the model method to revoke and save
            revoked_count += 1
        except Exception as e:
            modeladmin.message_user(
                request,
                f"Error revoking task {task.task_id}: {e}",
                level=messages.ERROR,
            )

    modeladmin.message_user(request, f"Successfully revoked {revoked_count} task(s).")


# --- ModelAdmin Class ---


@admin.register(ScheduledCeleryTasks)
class ScheduledCeleryTasksAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    # Fields displayed in the list view
    list_display = (
        "task_name",
        "eta",
        "db_status",  # Property to show DB status
        "live_status",  # Property to show live status
        "is_revoked",
        "task_id_link",
    )

    # Fields that can be filtered on
    list_filter = ("revoked", "status", "eta")

    # Fields that can be searched
    search_fields = ("task_name", "task_id")

    # Fields to display when viewing/editing a single record
    readonly_fields = (
        "task_name",
        "task_arguments",
        "eta",
        "task_id",
        "db_status",
        "live_status",
        "task_result",
        "task_error",
        "revoked"
    )

    # Custom actions
    actions = [refetch_status_action, revoke_tasks_action]

    # Disable "Add" as tasks should only be scheduled via the `schedule_task` method
    def has_add_permission(self, request):
        return False

    # --- Custom Display Properties ---

    @admin.display(description="DB Status")
    def db_status(self, obj):
        """Displays the stored database status with styling."""
        status = obj.status
        if status in ["SUCCESS"]:
            color = "green"
        elif status in ["FAILURE"]:
            color = "red"
        elif status in ["PENDING", "RETRY"]:
            color = "orange"
        else:
            color = "blue"

        return format_html(
            f'<span style="color: {color}; font-weight: bold;">{status}</span>'
        )

    @admin.display(description="Live Status")
    def live_status(self, obj):
        """Fetches the live status from Celery and displays it."""
        try:
            status = obj.fetch_status
        except Exception:
            status = "ERROR_FETCHING"

        color = "gray"
        if status in ["SUCCESS"]:
            color = "green"
        elif status in ["FAILURE", "REVOKED"]:
            color = "red"
        elif status in ["PENDING", "RETRY"]:
            color = "orange"
        elif status in ["STARTED"]:
            color = "blue"

        return format_html(
            f'<span style="color: {color}; font-weight: bold;">{status} (LIVE)</span>'
        )

    @admin.display(description="Revoked")
    def is_revoked(self, obj):
        """Displays the revoked status with an icon."""
        return obj.revoked

    is_revoked.boolean = True  # type: ignore[attr-defined]

    @admin.display(description="Task ID")
    def task_id_link(self, obj):
        """Allows copy-paste of the task ID."""
        return format_html(f'<code title="{obj.task_id}">{obj.task_id[:8]}...</code>')

    @admin.display(description="Result")
    def task_result(self, obj):
        """Displays stored result."""
        if obj.result:
            # Use a slightly monospace font for result/error
            return format_html(f"<pre>{obj.result}</pre>")
        return "N/A"

    @admin.display(description="Error/Traceback")
    def task_error(self, obj):
        """Displays stored error/traceback."""
        if obj.error:
            return format_html(f'<pre style="color: red;">{obj.error}</pre>')
        return "N/A"
