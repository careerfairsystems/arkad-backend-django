import jwt
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render

from user_models.models import User
from companies.models import Company
from student_sessions.models import StudentSession, StudentSessionApplication, StudentSessionTimeslot
from arkad.jwt_utils import jwt_decode


def company_admin_page(request, token):

    # Get user from jwt token given in the url
    payload = jwt_decode(token)
    user_id = payload.get("user_id")
    user = User.objects.get(id=user_id)

    if not user.is_company:
        raise PermissionDenied("Insufficient permissions")

    company_name = user.company.name
    
    applications = StudentSessionApplication.objects.filter(student_session__company__name=company_name)

    # TODO: Make this shorter
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
            "company_name": company_name, 
            "applications": application_info,
            "token": token
        }
    )
