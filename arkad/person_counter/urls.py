from django.urls import path
from .views import room_counter

urlpatterns = [
    path("", room_counter, name="person_counter"),
]
