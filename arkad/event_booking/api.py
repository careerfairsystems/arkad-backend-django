from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpRequest
from ninja import Router

from event_booking.models import Event, Ticket
from event_booking.schemas import EventSchema, TicketSchema, UseTicketSchema, EventUserInformation

router = Router(tags=["Events"])

@router.get("", response={200: list[EventSchema]})
def get_events(request: HttpRequest):
    """
    Returns a list of all events
    """
    return Event.objects.all()

@router.get("booked-events", response={200: list[EventSchema]})
def get_booked_events(request: HttpRequest):
    ts: list[Ticket] = request.user.tickets.prefetch_related('event').all()
    return [t.event for t in ts]

@router.get("{event_id}/", response={200: EventSchema, 404: str})
def get_event(request: HttpRequest, event_id: int):
    """
    Returns a single event
    """
    try:
        return Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return 404, "Event not found"

@router.get("/{event_id}/attending", response={200: list[EventUserInformation], 401: str})
def get_users_attending_event(request: HttpRequest, event_id: int):
    """
    Returns a list of names of the attending users, only if the calling user is staff
    """
    if not request.user.is_staff:
       return 401, "Not a staff user"
    return 200, [EventUserInformation(
        full_name=str(ticket.user), food_preferences=ticket.user.food_preferences
    ) for ticket in Ticket.objects.prefetch_related("user").filter(event_id=event_id)]

@router.get("get-ticket/{event_id}", response={200: UseTicketSchema, 401: str})
def get_event_ticket(request: HttpRequest, event_id: int):
    """
    Returns a ticket
    """
    tickets: QuerySet[Ticket] = request.user.tickets.prefetch_related('event').filter(event_id=event_id)
    if not tickets.exists():
        return 401, "Unauthorized"
    ticket: Ticket = tickets.first()  # Should only be one
    return UseTicketSchema(uuid=ticket.uuid)

@router.post("use-ticket", response={200: TicketSchema, 401: str})
def verify_ticket(request:HttpRequest, ticket: UseTicketSchema):
    """
    Returns 200 and the ticket schema which will now be used.

    If used or non-existing return 401.
    """
    if not request.user.is_staff:
        return 401, "This route is staff only."
    modified_tickets: int = Ticket.objects.filter(uuid=ticket.uuid, used=False).update(used=True)
    if modified_tickets == 1:
        return 200, Ticket.objects.get(uuid=ticket.uuid)
    return 401, "Unauthorized"


@router.post("acquire-ticket/{event_id}", response={200: EventSchema, 409: str, 404: str})
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
            if event.tickets.filter(user_id=request.user.id).exists():
                return 409, "You have already booked this event"
            ticket: Ticket = Ticket.objects.create(user=request.user, event=event)
            event.number_booked += 1
            event.tickets.add(ticket)
            event.save()
            return 200, event
        else:
            return 409, "Event already fully booked"

@router.post("remove-ticket/{event_id}", response={200: EventSchema, 409: str, 404: str})
def unbook_event(request: HttpRequest, event_id: int):
    """
    Unbook an event if you have a ticket.
    """
    with transaction.atomic():
        try:
            event: Event = Event.objects.select_for_update().get(id=event_id)
        except Event.DoesNotExist:
            return 404, "Event not found"

        # Delete the ticket
        deleted_count, _ = event.tickets.filter(user_id=request.user.id).delete()

        if deleted_count == 0:
            return 404, "You do not have a ticket for this event"

        # Update the counter
        event.number_booked -= 1
        event.save()

        return 200, event
