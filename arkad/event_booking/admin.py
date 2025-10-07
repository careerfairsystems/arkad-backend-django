from django.contrib import admin
from django.urls import path

from .models import Event, Ticket
from .views import create_lunch_event_view


class EventAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "create_lunch_event/",
                self.admin_site.admin_view(create_lunch_event_view),
                name="create_lunch_event",
            )
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_button"] = True
        return super().changelist_view(request, extra_context=extra_context)


admin.site.register(Event, EventAdmin)
admin.site.register(Ticket)
