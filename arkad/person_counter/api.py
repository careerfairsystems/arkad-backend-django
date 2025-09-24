from typing import Dict, List

from django.http import HttpRequest
from ninja.errors import HttpError

from arkad.customized_django_ninja import Router
from person_counter.models import RoomModel, PersonCounter

router = Router(tags=["Person Counter"])


@router.get("rooms", auth=None)
def list_rooms(request: HttpRequest):
    """List available rooms with current counters. Requires staff via session auth."""
    user = getattr(request, "user", None)
    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_staff", False):
        raise HttpError(403, "Require staff status")

    rooms: List[Dict[str, int | str]] = []
    for room in RoomModel.objects.all():
        last = PersonCounter.get_last(room.name)
        rooms.append({"name": room.name, "counter": last.count if last else 0})
    return {"rooms": rooms}
