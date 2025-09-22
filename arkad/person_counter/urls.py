from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="person_counter"),
    path("room-counter/", views.room_counter, name="room_counter_demo"),
]
