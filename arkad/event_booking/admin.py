from typing import Any

from django.contrib import admin
from django.urls import path

from .models import Event, Ticket
from .views import create_lunch_event_view


class EventAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    actions = ["revoke_and_reschedule_tasks_action"]

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


admin.site.register(Event, EventAdmin)
admin.site.register(Ticket)
