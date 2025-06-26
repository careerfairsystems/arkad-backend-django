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
