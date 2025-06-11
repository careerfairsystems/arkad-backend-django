from django.http import Http404
from django.shortcuts import get_object_or_404, render

from companies.models import Company
from student_sessions.models import StudentSession, StudentSessionApplication, StudentSessionTimeslot

def company_admin_page(request, company_name:str):

    company = get_object_or_404(Company, name=company_name) #The name should be replaced with a generated token that is in the company model
    
    applications = StudentSessionApplication.objects.filter(student_session__company__name= company.name)

    #I application ska man kunna se: Namn, CV (rendera direkt i skärmen?), Motivational letter.

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
            "company": company_name,
            "applications": application_info
        }
    )