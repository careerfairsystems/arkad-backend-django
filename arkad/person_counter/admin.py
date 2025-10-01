# Register your models here.

from django.contrib import admin
from .models import PersonCounter, RoomModel


@admin.register(PersonCounter)
class PersonCounterAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("room", "created_at", "count", "delta")
    list_filter = ("room", "created_at")
    search_fields = ("room__name",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)


admin.site.register(RoomModel)
