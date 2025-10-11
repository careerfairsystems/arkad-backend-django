from django.contrib import admin
from notifications.models import NotificationLog

# Create a custom admin class for NotificationLog,
# No one should have change permission but create is granted to superusers
# Created notification logs are sent out automatically via FCM and/or email

@admin.register(NotificationLog)
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
    readonly_fields = (
        "target_user",
        "notification_topic",
        "title",
        "body",
        "email_sent",
        "fcm_sent",
        "sent_at",
    )

    def has_add_permission(self, request):
        # Only superusers can add notification logs
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        # No one can change notification logs
        return False

    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete notification logs
        return request.user.is_superuser