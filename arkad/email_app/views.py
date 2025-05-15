from django.shortcuts import render

# Create your views here.

def test_reset(request):
    return render(request, 'email_app/reset.html', {"reset_link": "https://example.com/reset", "name": "asdas"})

def test_sign_up(request):
    return render(request, 'email_app/sign_up.html', {"digits": [1,2,3,4,5,6]})




