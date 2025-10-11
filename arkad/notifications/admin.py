from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from arkad.settings import DEBUG
from notifications.models import Notification

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
