from django.urls import path
from django.contrib.auth import views as auth_views

from arkad.settings import DEBUG
from user_models.views import delete_account

debugging_urls = [
    path(
        "reset-password-sent/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="password_reset_done.html"
        ),
        name="password_reset_done",
    ),
]

urlpatterns = [
    *(debugging_urls if DEBUG else []),
    path(
        "reset-password/",
        auth_views.PasswordResetView.as_view(template_name="password_reset.html"),
        name="reset_password",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset_password_complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path(
        "delete-account/",
        delete_account,
        name="delete_account",
    ),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="login.html"),
        name="login",
    ),
]
