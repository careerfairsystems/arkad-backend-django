from django.shortcuts import render

from student_sessions.models import StudentSession, StudentSessionApplication, StudentSessionTimeslot

def company_admin_page(request):
    
    applications = StudentSessionApplication.objects.all()

    #I application ska man kunna se: Namn, CV (rendera direkt i skärmen?), Motivational letter. Bild?

    application_info = {
        "name": "",
        "cv": "",
        "motivational_letter":""
    }

    return render(
        request=request,
        template_name="company_admin_page.html",
        context={"applications": applications}
    )