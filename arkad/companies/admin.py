from typing import Any

from django.contrib import admin
from django.http import HttpResponse, HttpRequest

from companies.models import Job, Company
from django.urls import reverse


class ArrayFieldListFilter(admin.SimpleListFilter):
    """Base filter for ArrayField to show unique values across all arrays."""

    def lookups(self, request: HttpRequest, model_admin: Any) -> Any:
        """
        Returns a list of tuples with all unique values found in the array field.
        """
        # Get all unique values from the array field
        qs = model_admin.get_queryset(request)
        all_values = set()

        for obj in qs:
            field_value = getattr(obj, self.parameter_name, None)  # type: ignore[arg-type]
            if field_value:
                all_values.update(field_value)

        # Return sorted list of tuples (value, display_name)
        return sorted([(val, val) for val in all_values])

    def queryset(self, request, queryset):  # type: ignore[no-untyped-def]
        """
        Filter queryset to include only objects where the array contains the selected value.
        """
        if self.value():
            # Use __contains to check if the value is in the array
            filter_kwargs = {f"{self.parameter_name}__contains": [self.value()]}
            return queryset.filter(**filter_kwargs)
        return queryset


class DesiredDegreesFilter(ArrayFieldListFilter):
    title = "desired degrees"
    parameter_name = "desired_degrees"


class DesiredProgrammeFilter(ArrayFieldListFilter):
    title = "desired programme"
    parameter_name = "desired_programme"


class DesiredCompetencesFilter(ArrayFieldListFilter):
    title = "desired competences"
    parameter_name = "desired_competences"

class PositionsFilter(ArrayFieldListFilter):
    title = "positions"
    parameter_name = "positions"

class IndustriesFilter(ArrayFieldListFilter):
    title = "industries"
    parameter_name = "industries"


# Register your models here.
class CompanyAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    search_fields = ["name"]
    list_display = ["name", "website", "company_email"]
    list_filter = [
        DesiredDegreesFilter,
        DesiredProgrammeFilter,
        DesiredCompetencesFilter,
        PositionsFilter,
        IndustriesFilter,
    ]

    def changelist_view(
        self, request: HttpRequest, extra_context: Any = None
    ) -> HttpResponse:
        extra_context = extra_context or {}
        extra_context["upload_url"] = reverse("admin:jexpo_sync_upload_companies")
        return super().changelist_view(request, extra_context=extra_context)


admin.site.register(Job)
admin.site.register(Company, CompanyAdmin)
