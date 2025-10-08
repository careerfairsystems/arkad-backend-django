# Create your views here.


from django.shortcuts import render

from email_app.utils import get_base_url


def test_reset(request):
    return render(
        request,
        "email_app/reset.html",
        {
            "reset_link": "https://example.com/reset",
            "name": "asdas",
            "base_url": get_base_url(request),
        },
    )


def test_sign_up(request):
    return render(
        request,
        "email_app/sign_up.html",
        {"digits": [1, 2, 3, 4, 5, 6], "base_url": get_base_url(request)},
    )


def test_generic_information(request):
    return render(
        request,
        "email_app/generic_information_email.html",
        {
            "name": "John Doe",
            "greeting": "Welcome to ARKAD!",
            "heading": "Your registration has been confirmed",
            "message": "Thank you for registering for the ARKAD Career Fair 2025. We are excited to have you join us!<br><br>The event will take place on <strong>November 11-12, 2025</strong> at Kårhuset in Lund.",
            "button_text": "View Event Details",
            "button_link": "https://www.arkadtlth.se",
            "note": "If you have any questions, please don't hesitate to contact us.",
            "base_url": get_base_url(request),
        },
    )
