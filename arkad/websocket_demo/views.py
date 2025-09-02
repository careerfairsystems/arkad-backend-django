from django.shortcuts import render


def index(request):
    """Render the WebSocket demo interface"""
    return render(request, 'websocket_demo/index.html')


def room_counter(request):
    """Render the room counter demo interface"""
    return render(request, 'websocket_demo/room_counter.html')
