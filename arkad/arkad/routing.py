from django.urls import re_path
from arkad.consumers import PingConsumer, RoomCounterConsumer

websocket_urlpatterns = [
    re_path(r"ws/ping/$", PingConsumer.as_asgi()),
    re_path(r"ws/counter/$", RoomCounterConsumer.as_asgi()),
]
