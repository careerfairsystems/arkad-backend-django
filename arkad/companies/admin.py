from typing import Any

from django.contrib import admin
from django.http import HttpResponse, HttpRequest

from companies.models import Job, Company
from django.urls import reverse


# Register your models here.
class CompanyAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    search_fields = ["name"]
    list_display = ["name", "website", "company_email"]
    list_filter = [
        "desired_degrees",
    ]

    def changelist_view(
        self, request: HttpRequest, extra_context: Any = None
    ) -> HttpResponse:
        extra_context = extra_context or {}
        extra_context["upload_url"] = reverse("admin:jexpo_sync_upload_companies")
        return super().changelist_view(request, extra_context=extra_context)


admin.site.register(Job)
admin.site.register(Company, CompanyAdmin)
