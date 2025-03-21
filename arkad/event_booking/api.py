import datetime

from django.db import transaction
from django.http import HttpRequest
from django.utils import timezone
from ninja import Router

from arkad.jwt_utils import jwt_encode
from event_booking.models import Event
from event_booking.schemas import EventSchema

router = Router(tags=["Events"])

@router.get("", response={200: list[EventSchema]})
def get_events(request: HttpRequest):
    """
    Returns a list of all events
    """
    return Event.objects.all()


@router.get("booked-events", response={200: list[EventSchema]})
def get_booked_events(request: HttpRequest):
    return request.user.event_set.all()

@router.get("{event_id}", response={200: EventSchema, 404: str})
def get_event(request: HttpRequest, event_id: int):
    """
    Returns a single event
    """
    try:
        return Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return 404, "Event not found"

@router.get("token/{event_id}", response={200: str, 401: str})
def get_token(request: HttpRequest, event_id: int):
    if request.user.event_set.filter(id=event_id).exists():
        return 200, jwt_encode({
            "event_id": event_id,
            "user_id": request.user.id,
            "ticket_is_valid": True,
            "expires_at": timezone.now() + datetime.timedelta(minutes=1)
        })
    return 401, "Not authorized"

@router.post("/events/{event_id}/book", response={200: EventSchema, 409: str})
def book_event(request: HttpRequest, event_id: int):
    """
    Book an event if it is not already fully booked
    """
    with transaction.atomic():
        try:
            event: Event = Event.objects.filter(id=event_id).select_for_update().get(id=event_id)
        except Event.DoesNotExist:
            return 404, "Event not found"
        if event.number_booked < event.capacity:
            if event.attending.filter(id=request.user.id).exists():
                return 409, "You have already booked this event"
            event.number_booked += 1
            event.attending.add(request.user)
            event.save()
            return 200, event
        else:
            return 409, "Event already fully"

@router.post("/events/{event_id}/unbook", response={200: EventSchema, 409: str})
def unbook_event(request: HttpRequest, event_id: int):
    """
    Unbook an event if you have a ticket
    """
    with transaction.atomic():
        try:
            event: Event = request.user.event_set.select_for_update().get(id=event_id)
        except Event.DoesNotExist:
            return 404, "Event not found"
        event.number_booked -= 1
        event.attending.remove(request.user)
        event.save()
        return 200, event
