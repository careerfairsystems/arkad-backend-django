from typing import Dict, List, Union

from django.http import HttpRequest
from ninja.security import SessionAuthIsStaff

from arkad.customized_django_ninja import Router
from person_counter.models import RoomModel, PersonCounter

router = Router(tags=["Person Counter"])


@router.get("rooms", auth=SessionAuthIsStaff())
def list_rooms(request: HttpRequest):
    """List available rooms.

    Public endpoint: returns a list of rooms for everyone. If the requester is
    an authenticated staff user, include the current counter value for each
    room under the "counter" key. Non-staff/anonymous users receive objects
    containing only the "name" field.
    """
    rooms: List[Dict[str, Union[str, int]]] = []
    for room in RoomModel.objects.all():
        last = PersonCounter.get_last(room.name)
        rooms.append({"name": room.name, "counter": last.count if last else 0})
    return {"rooms": rooms}
