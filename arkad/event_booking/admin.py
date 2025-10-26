from typing import Any
from django.contrib import admin
from django.db.models import QuerySet
from django.urls import path
from django.http import HttpRequest
from import_export import resources, fields
from import_export.admin import ExportMixin
from import_export.widgets import BooleanWidget

from .models import Event, Ticket
from .views import create_lunch_event_view


# --- Ticket Export Resource ---
class TicketExportResource(resources.ModelResource):  # type: ignore[type-arg]
    """
    Resource for exporting Ticket data related to a specific Event.
    """

    # Explicitly define the id field
    uuid = fields.Field(attribute="uuid", column_name="ID")
    user_name = fields.Field(attribute="user", column_name="User Name")
    email = fields.Field(attribute="user__email", column_name="Email")
    used = fields.Field(
        attribute="used", column_name="Ticket Used", widget=BooleanWidget()
    )
    food_preferences = fields.Field(
        attribute="user__food_preferences", column_name="Food Preferences"
    )
    # Use the correct field name 'event_name' here
    event_name = fields.Field(attribute="event__name", column_name="Event Name")

    class Meta:
        model = Ticket
        # Use the correct field names in fields and export_order
        fields = (
            "uuid",
            "user_name",
            "email",
            "used",
            "food_preferences",
            "event_name",
        )
        export_order = (
            "uuid",
            "event_name",
            "user_name",
            "email",
            "used",
            "food_preferences",
        )
        # We only want export, not import
        import_id_fields = []  # type: ignore[var-annotated]

    def get_queryset(self):  # type: ignore[no-untyped-def]
        """
        Ensure related user data is fetched efficiently.
        """
        # Ensure that the queryset passed from admin is used
        qs = super().get_queryset()
        return (
            qs.select_related("user", "event")
            if qs is not None
            else Ticket.objects.none()
        )


# --- Event Admin ---
class TicketInline(admin.TabularInline):  # type: ignore[type-arg]
    """Inline view for Tickets within EventAdmin"""

    model = Ticket
    extra = 0  # Don't show extra empty forms
    readonly_fields = ("user", "uuid", "used")  # Make fields read-only
    can_delete = False  # Prevent deleting tickets from here

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:  # type: ignore[no-untyped-def]
        return False  # Disable adding tickets directly in the inline view


@admin.register(Event)  # Use decorator for registration
class EventAdmin(ExportMixin, admin.ModelAdmin):  # type: ignore[type-arg, misc] # Inherit ExportMixin
    resource_classes = [TicketExportResource]  # Use the custom resource for export
    list_display = (
        "name",
        "type",
        "start_time",
        "capacity",
        "number_booked",
        "company",
    )
    list_filter = ("type", "start_time", "company")
    search_fields = ("name", "description", "company__name")
    actions = ["revoke_and_reschedule_tasks_action"]

    readonly_fields = ("number_booked", "notify_registration_opening")

    def get_export_queryset(self, request: HttpRequest) -> QuerySet[Ticket]:
        """
        Override to export tickets related to the *selected* events.
        """
        event_ids = request.POST.getlist(admin.helpers.ACTION_CHECKBOX_NAME)
        if not event_ids:
            list_display_qs = self.get_queryset(request)
            return Ticket.objects.filter(event__in=list_display_qs).select_related(
                "user", "event"
            )
        return Ticket.objects.filter(event_id__in=event_ids).select_related(
            "user", "event"
        )

    def get_export_filename(self, request: HttpRequest, queryset, file_format):  # type: ignore[no-untyped-def, override]
        """
        Customize the export filename to include event name(s).
        """
        event_ids = list(queryset.values_list("event_id", flat=True).distinct())
        if len(event_ids) == 1:
            try:
                event = Event.objects.get(pk=event_ids[0])
                event_name = event.name.replace(" ", "_")
                return f"{event_name}_tickets.{file_format.get_extension()}"
            except Event.DoesNotExist:
                pass
        elif len(event_ids) > 1:
            return f"multiple_events_tickets.{file_format.get_extension()}"
        opts = self.model._meta
        return (
            f"{opts.app_label}_{opts.model_name}_export.{file_format.get_extension()}"
        )

    def get_urls(self) -> list[Any]:
        urls = super().get_urls()
        custom_urls = [
            path(
                "create_lunch_event/",
                self.admin_site.admin_view(create_lunch_event_view),
                name="create_lunch_event",
            )
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):  # type: ignore[no-untyped-def]
        extra_context = extra_context or {}
        extra_context["show_button"] = True
        return super().changelist_view(request, extra_context=extra_context)

    def revoke_and_reschedule_tasks_action(self, request, queryset):  # type: ignore[no-untyped-def]
        for event in queryset:
            event.revoke_and_reschedule_tasks()
        self.message_user(
            request, f"Revoked and rescheduled tasks for {queryset.count()} event(s)."
        )

    revoke_and_reschedule_tasks_action.short_description = (  # type: ignore[attr-defined]
        "Revoke and reschedule all scheduled tasks for selected events"
    )


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("event", "user", "used", "uuid")
    list_filter = ("event", "used")
    search_fields = (
        "event__name",
        "user__username",
        "user__first_name",
        "user__last_name",
        "uuid",
    )
    readonly_fields = ("uuid", "event", "user")
