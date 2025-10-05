from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_http_methods

from user_models.models import User


@login_required
@require_http_methods(["GET", "POST"])
def delete_account(request: HttpRequest) -> HttpResponse:
    """
    Allow users to delete their account and all associated data.
    Staff and company users can view the page but cannot delete their accounts - they must contact a superadmin.
    """
    user: User = request.user  # type: ignore

    # Prevent staff users and company users from deleting their accounts via POST
    if request.method == "POST":
        if user.is_staff or user.is_company:
            messages.error(request, "Staff and company users cannot delete their accounts through this interface. Please contact a superadmin.")
            return redirect('/user/delete-account/')

        # Delete the user and all associated data
        user.delete()
        messages.success(request, "Your account has been successfully deleted.")
        return redirect('/')

    # GET request - show the confirmation page
    # Pass a flag to indicate if user can delete their account
    can_delete = not (user.is_staff or user.is_company)
    return render(request, 'delete_account.html', {'user': user, 'can_delete': can_delete})
