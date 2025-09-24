from typing import Dict, List

from django.http import HttpRequest
from ninja.errors import HttpError

from arkad.customized_django_ninja import Router
from person_counter.models import RoomModel, PersonCounter

router = Router(tags=["Person Counter"])


@router.get("rooms", auth=None)
def list_rooms(request: HttpRequest):
    """List available rooms with current counters."""
    # Allow anyone (including anonymous) to fetch available rooms so the
    # frontend can populate the dropdown for all users.
    # If you want to restrict this later, add auth checks here.

    rooms: List[Dict[str, int | str]] = []
    for room in RoomModel.objects.all():
        last = PersonCounter.get_last(room.name)
        rooms.append({"name": room.name, "counter": last.count if last else 0})
    return {"rooms": rooms}
