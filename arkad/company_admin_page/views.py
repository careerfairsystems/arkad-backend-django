from django.shortcuts import render

def company_admin_page(request):
    return render(
        request=request,
        template_name="company_admin_page.html",
        context={}
    )