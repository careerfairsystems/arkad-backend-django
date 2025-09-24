from django.urls import path
from .views import index, room_counter

urlpatterns = [
    path("", index, name="person_counter"),
    path("room-counter/", room_counter, name="room_counter_demo"),
]
