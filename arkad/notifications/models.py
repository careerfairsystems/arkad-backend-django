from django.db import models


class NotificationLog(models.Model):
    target_user = models.ForeignKey(
        "user_models.User",
        on_delete=models.CASCADE,
        related_name="notification_logs",
        null=True,
        blank=True,
    )
    notification_topic = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    body = models.TextField()

    email_sent = models.BooleanField(default=False)
    fcm_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
