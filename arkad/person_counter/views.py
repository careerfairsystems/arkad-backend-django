from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def index(request: HttpRequest) -> HttpResponse:
    """Render the WebSocket demo interface"""
    return render(request, "person_counter/index.html")


def room_counter(request: HttpRequest) -> HttpResponse:
    """Render the room counter demo interface"""
    return render(request, "person_counter/room_counter.html")
