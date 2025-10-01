import os
from functools import partial
from typing import Any

from django.db import models
from django.core.exceptions import ValidationError
from arkad.utils import unique_file_upload_path
from user_models.models import User


def validate_json_file(value: Any) -> None:
    """Validate that the uploaded file is a JSON file"""
    if not value.name.lower().endswith(".json"):
        raise ValidationError("Only JSON files are allowed.")

    # Check file size (limit to 50MB)
    if value.size > 50 * 1024 * 1024:
        raise ValidationError("File size cannot exceed 50MB.")


class CompanySyncUpload(models.Model):
    """Model to handle JSON file uploads for company synchronization"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    file = models.FileField(
        upload_to=partial(unique_file_upload_path, "jexpo_sync"),
        help_text="Upload a JSON file containing company data",
        validators=[validate_json_file],
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="company_sync_uploads",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    companies_processed = models.IntegerField(default=0)
    companies_created = models.IntegerField(default=0)
    companies_updated = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "Company Sync Upload"
        verbose_name_plural = "Company Sync Uploads"
        permissions = [
            ("can_upload_company_sync", "Can upload company sync files"),
        ]

    def __str__(self) -> str:
        return f"Upload {self.id} - {self.file.name} ({self.status})"

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        """Override delete to ensure file is removed from filesystem"""
        if self.file:
            try:
                if os.path.exists(self.file.path):
                    os.remove(self.file.path)
            except (ValueError, OSError):
                # File might not exist or path might be invalid
                pass
        return super().delete(*args, **kwargs)
