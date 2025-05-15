from django.shortcuts import render

def test_view(request): 
    return render(request, 'email_app/sign_up.html', {"reset_link": "www.example.com", "name": "asdas"})

# Create your views here.
