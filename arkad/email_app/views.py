from django.shortcuts import render

def test_view(request):
    return render(request, 'email_app/sign_up.html', {"reset_link": "{{ protocol }}://{{ domain }}{% url 'password_reset_confirm' uidb64=uid token=token %}", "name": "asdas"})

# Create your views here.
