"""
URL configuration for arkad project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from email_app.views import (
    test_reset,
    test_sign_up,
    test_generic_information,
    test_event_closing_reminder,
    test_event_reminder_tomorrow,
    test_event_reminder_one_hour,
    test_event_selection_student_session,
    test_event_selection_company_visit,
)

urlpatterns = [
    path("test/reset", test_reset, name="test_reset"),
    path("test/sign_up", test_sign_up, name="test_sign_up"),
    path(
        "test/generic_information",
        test_generic_information,
        name="test_generic_information",
    ),
    path(
        "test/event_closing_reminder",
        test_event_closing_reminder,
        name="test_event_closing_reminder",
    ),
    path(
        "test/event_reminder_tomorrow",
        test_event_reminder_tomorrow,
        name="test_event_reminder_tomorrow",
    ),
    path(
        "test/event_reminder_one_hour",
        test_event_reminder_one_hour,
        name="test_event_reminder_one_hour",
    ),
    path(
        "test/event_selection_student_session",
        test_event_selection_student_session,
        name="test_event_selection_student_session",
    ),
    path(
        "test/event_selection_company_visit",
        test_event_selection_company_visit,
        name="test_event_selection_company_visit",
    ),
]
