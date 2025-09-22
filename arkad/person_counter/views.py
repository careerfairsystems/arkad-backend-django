from django.shortcuts import render


def index(request):
    """Render the WebSocket demo interface"""
    return render(request, "person_counter/index.html")


def room_counter(request):
    """Render the room counter demo interface"""
    return render(request, "person_counter/room_counter.html")
