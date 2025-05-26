from django.urls import path
from company_admin_page.views import company_admin_page

urlpatterns = [
    path("admin/", view=company_admin_page , name="company_admin_page")
]