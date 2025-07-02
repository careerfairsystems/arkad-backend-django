from django.core.exceptions import PermissionDenied
from django.shortcuts import render

from user_models.models import User
from student_sessions.models import StudentSessionApplication
from arkad.jwt_utils import jwt_decode


def company_admin_page(request, token):

    # Get user from jwt token given in the url
    user_id = jwt_decode(token).get("user_id")

    user = User.objects.get(id=user_id)
    if not user.is_company:
        raise PermissionDenied("Insufficient permissions")

    company_name = user.company.name
    
    applications = StudentSessionApplication.objects.filter(student_session__company__name=company_name)
    
    applications_info = [{
                "applicantid": application.user.id,
                "name":f"{application.user.first_name} {application.user.last_name}",
                "programme": application.user.programme,
                "study_year": application.user.study_year,
                "master_title" : application.user.master_title,
                "cv": application.cv,
                "motivation_text": application.motivation_text,
                "status": application.status,
            } for application in applications]

    return render(
        request=request,
        template_name="company_admin_page.html",
        context={
            "company_name": company_name, 
            "applications": applications_info,
            "token": "Bearer " + token
        }
    )
