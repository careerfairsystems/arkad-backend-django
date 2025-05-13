from django.shortcuts import render

def test_view(request):
    return render(request, 'email_app/reset_email.html', {"reset_link": "https://example.com/reset", "name": "asdas"})

# Create your views here.
