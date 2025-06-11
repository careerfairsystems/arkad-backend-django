from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render

from user_models.models import User
from companies.models import Company
from student_sessions.models import StudentSession, StudentSessionApplication, StudentSessionTimeslot

def company_admin_page(request, token):
    #This is currently broken. 
    #The token need to be decoded to extract the user id?
    user = request.user

    if not user.is_company:
        raise PermissionDenied("Insufficient permissions")

    username = user.company.name
    
    applications = StudentSessionApplication.objects.filter(student_session__company__name=username)
    token = user.create_jwt_token()

    #TODO: Fix so that "status" is visible on admin page

    application_info = []
    for application in applications:
        application_info.append({
            "applicantId": application.user.id,
            "name":f"{application.user.first_name} {application.user.last_name}",
            "cv": "CV", #TODO: Add cv file (preview or download?)
            "motivation_text": application.motivation_text,
            "status": application.status,
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