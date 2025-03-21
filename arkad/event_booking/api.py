from django.db import transaction
from django.http import HttpRequest
from ninja import Router

from event_booking.models import Event
from event_booking.schemas import EventSchema

router = Router(tags=["Events"])

@router.get("/events", response={200: list[EventSchema]})
def get_events(request: HttpRequest):
    """
    Returns a list of all events
    """
    return Event.objects.all()

@router.get("/events/{event_id}", response={200: EventSchema, 404: str})
def get_event(request: HttpRequest, event_id: int):
    """
    Returns a single event
    """
    try:
        return Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return 404, "Event not found"

@router.post("/events/{event_id}/book", response={200: EventSchema, 409: str})
def book_event(request: HttpRequest, event_id: int):
    """
    Book an event if it is not already fully booked
    """
    with transaction.atomic():
        try:
            event: Event = Event.objects.select_for_update().get(id=event_id)
        except Event.DoesNotExist:
            return 404, "Event not found"
        if event.number_booked < event.capacity:
            if event.attending.filter(id=request.user.id).exists():
                return 409, "You have already booked this event"
            event.number_booked += 1
            event.attending.add(request.user)
            event.save()
        else:
            return 409, "Event already fully"

