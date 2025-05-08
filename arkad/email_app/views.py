from django.shortcuts import render

def test_view(request):
    return render(request, 'signup_email.html', {"reset_link": "https://example.com/reset"})

# Create your views here.
