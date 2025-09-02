from django.shortcuts import render


def index(request):
    """Render the WebSocket demo interface"""
    return render(request, 'websocket_demo/index.html')
