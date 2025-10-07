from django.urls import path
from . import views

app_name = "event_booking"

urlpatterns = [
    path(
        "create_lunch_event/", views.create_lunch_event_view, name="create_lunch_event"
    ),
]
