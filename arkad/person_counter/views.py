from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

@staff_member_required
def room_counter(request: HttpRequest) -> HttpResponse:
    """Render the room counter demo interface"""
    return render(request, "person_counter/room_counter.html")

