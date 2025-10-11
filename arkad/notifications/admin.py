from django.contrib import admin

from arkad.settings import DEBUG
from notifications.models import Notification

# Create a custom admin class for NotificationLog,
# No one should have change permission but create is granted to superusers
# Created notification logs are sent out automatically via FCM and/or email

@admin.register(Notification)
class NotificationLogAdmin(admin.ModelAdmin):
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

    def has_add_permission(self, request):
        # Only superusers can add notification logs
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        # No one can change notification logs
        return False

    def has_delete_permission(self, request, obj=None):
        # Only possible to delete in DEBUG mode
        return DEBUG