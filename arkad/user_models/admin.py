from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.action(description="Send url to company admin page.")
def send_urls(modeladmin, request, queryset) -> str:
    """
    Generates URLs to company admin page with a JWT, and sends an email with the url to user.
    Skips users that are not part of a company.
    """
    for user in queryset:
        if user.is_company: #Skip users that are not part of a company (maybe throw error instead?)
            company_admin_url = generate_url(request, user)
            user.email_user(
                "ARKAD Company admin page", 
                f"This is the URL to your company admin page for ARKAD. Do not share with anyone: {company_admin_url}"
                )


def generate_url(request, user: User) -> str:
    domain = f"{request.scheme}://{request.get_host()}"

    token = user.create_jwt_token(expiry_days=30) #Expires in one month
    token = token.split(" ", 1)[1] 

    return f"{domain}/company/admin/{token}"


class CustomUserAdmin(UserAdmin):
    list_display = ["id", "username", "email", "first_name", "last_name", "company", "is_active", "is_staff", "is_superuser"]
    list_filter = ["is_staff", "is_superuser", "is_active"]
    actions = [send_urls]


admin.site.register(User, CustomUserAdmin)
