from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.http import HttpRequest
from typing import Any
import secrets

from .models import User, StaffEnrollmentToken, StaffEnrollmentUsage


class UserAdmin(BaseUserAdmin):  # type: ignore[type-arg]
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_student",
        "is_company_user",
        "programme",
        "study_year",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "is_student",
        "programme",
        "study_year",
        "groups",
    )
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "email", "food_preferences")},
        ),
        (
            "Student info",
            {
                "fields": (
                    "is_student",
                    "programme",
                    "study_year",
                    "master_title",
                    "linkedin",
                )
            },
        ),
        ("Files", {"fields": ("cv", "profile_picture")}),
        ("Company", {"fields": ("company",)}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        ("Notifications", {"fields": ("fcm_token",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_student",
                ),
            },
        ),
    )

    actions = ["generate_staff_enrollment_link"]

    def is_company_user(self, obj: User) -> bool:
        return obj.is_company

    is_company_user.boolean = True  # type: ignore[attr-defined]
    is_company_user.short_description = "Company User"  # type: ignore[attr-defined]

    def generate_staff_enrollment_link(
        self, request: HttpRequest, queryset: Any
    ) -> None:
        """Generate a secure staff enrollment link"""
        # Only allow superusers to generate enrollment links
        if not request.user.is_superuser:
            messages.error(
                request, "Only superusers can generate staff enrollment links."
            )
            return

        # Generate a cryptographically secure token
        token = secrets.token_urlsafe(32)

        # Create the token in database with expiration
        from django.utils import timezone
        from datetime import timedelta

        StaffEnrollmentToken.objects.create(
            token=token,
            created_by=request.user,
            expires_at=timezone.now() + timedelta(days=7),
        )

        # Generate the full URL
        enrollment_url = request.build_absolute_uri(
            reverse("staff_enrollment", kwargs={"token": token})
        )

        # Show the link to the admin
        messages.success(
            request,
            format_html(
                "Staff enrollment link generated (valid for 7 days):<br><strong>{0}</strong><br>"
                '<a href="{1}" target="_blank">Open in new tab</a>',
                enrollment_url,
                enrollment_url,
            ),
        )

    generate_staff_enrollment_link.short_description = "Generate staff enrollment link"  # type: ignore[attr-defined]

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Only superusers can add new users"""
        return request.user.is_superuser

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Superusers can change any user, staff can only change themselves"""
        if request.user.is_superuser:
            return True
        # Staff can only change their own account
        if obj is not None and request.user.is_staff:
            return bool(obj.pk == request.user.pk)
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Only superusers can delete users"""
        return request.user.is_superuser


class StaffEnrollmentUsageInline(admin.TabularInline):  # type: ignore[type-arg]
    model = StaffEnrollmentUsage
    extra = 0
    readonly_fields = ("user", "created_at")
    can_delete = False

    def has_add_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False


class StaffEnrollmentTokenAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "token_preview",
        "created_by",
        "created_at",
        "expires_at",
        "is_active",
        "usage_count",
    )
    list_filter = ("is_active", "created_at", "expires_at")
    search_fields = ("token", "created_by__username")
    readonly_fields = ("token", "created_by", "created_at")
    ordering = ("-created_at",)
    inlines = [StaffEnrollmentUsageInline]

    def token_preview(self, obj: StaffEnrollmentToken) -> str:
        return f"{obj.token[:16]}..."

    token_preview.short_description = "Token"  # type: ignore[attr-defined]

    def usage_count(self, obj: StaffEnrollmentToken) -> int:
        return obj.usages.count()

    usage_count.short_description = "Times Used"  # type: ignore[attr-defined]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Only superusers can change staff enrollment tokens"""
        return request.user.is_superuser

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Only superusers can delete staff enrollment tokens"""
        return request.user.is_superuser


admin.site.register(User, UserAdmin)
admin.site.register(StaffEnrollmentToken, StaffEnrollmentTokenAdmin)
