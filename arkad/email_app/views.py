from django.shortcuts import render

def test_view(request):
    return render(request, 'email_app/sign_up.html', {"reset_link": "https://example.com/reset"})

# Create your views here.
