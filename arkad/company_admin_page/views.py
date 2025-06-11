from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render

from user_models.models import User
from companies.models import Company
from student_sessions.models import StudentSession, StudentSessionApplication, StudentSessionTimeslot

def company_admin_page(request, user_id):

    user = get_object_or_404(User, id=user_id)

    if not user.is_company:
        raise PermissionDenied("Insufficient permissions")

    username = user.company.name
    #company = get_object_or_404(Company, name=user.company.name) #The name should be replaced with a generated token that is in the company model
    
    applications = StudentSessionApplication.objects.filter(student_session__company__name=username)
    token = user.create_jwt_token()

    #I application ska man kunna se: Namn, CV (rendera direkt i skärmen?), Motivational letter och ifall den är accepted/rejected.

    application_info = []
    for application in applications:
        application_info.append({
            "applicantId": application.user.id,
            "name":f"{application.user.first_name} {application.user.last_name}",
            "cv": "CV", #TODO: Add cv file (preview or download?)
            "motivation_text": application.motivation_text,
        })     

    return render(
        request=request,
        template_name="company_admin_page.html",
        context={
            "company_name": username,
            "applications": application_info,
            "token": token
        }
    )