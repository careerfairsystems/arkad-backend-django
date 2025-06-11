from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from .models import User


# Register your models here.
#admin.site.register(User)


#TODO: Add admin action for creating a URL with users jwt token. create jwt token with loong expiry
@admin.action(description="Generate urls for companies.")
def generate_urls(modeladmin, request, queryset) -> str:
    updated = queryset.update(first_name="AnotherCompany")
    #modeladmin.message_user(request, f"{updated}", messages.success)


class CustomUserAdmin(UserAdmin):
    list_display = ["id", "username", "email", "first_name", "last_name", "company", "is_active", "is_staff"]
    list_filter = ["is_staff", "is_superuser", "is_active"]
    actions = [generate_urls]


#admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)