from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from arkad.auth import OPTIONAL_AUTH
from arkad.customized_django_ninja import Router, ListType
from user_models.models import AuthenticatedRequest
from event_booking.models import Event, Ticket
from event_booking.schemas import (
    EventSchema,
    TicketSchema,
    UseTicketSchema,
    EventUserInformation,
    EventUserStatus,
)

router = Router(tags=["Events"])


@router.get("", response={200: ListType[EventSchema]}, auth=OPTIONAL_AUTH)
def get_events(request: AuthenticatedRequest):
    """
    Returns a list of all events
    """
    if not request.user.is_authenticated:
        return Event.objects.all()
    events: QuerySet[Event] = Event.objects.prefetch_related("tickets").all()
    result: list[EventSchema] = []
    for event in events:
        schema = EventSchema.from_orm(event)
        user_ticket: Ticket | None = event.tickets.filter(
            user_id=request.user.id
        ).first()
        if user_ticket is not None:
            schema.status = user_ticket.status()
        result.append(schema)
    return result


@router.get("booked-events", response={200: ListType[EventSchema]})
def get_booked_events(request: AuthenticatedRequest):
    ts: QuerySet[Ticket] = request.user.ticket_set.prefetch_related("event").all()

    result: list = []
    for ticket in ts:
        event: Event = ticket.event
        schema = EventSchema.from_orm(event)
        schema.status = ticket.status()
        result.append(schema)

    return result


@router.get("{event_id}/", response={200: EventSchema, 404: str}, auth=OPTIONAL_AUTH)
def get_event(request: AuthenticatedRequest, event_id: int):
    """
    Returns a single event
    """
    try:
        event = Event.objects.get(id=event_id)
        schema = EventSchema.from_orm(event)
        if request.user.is_authenticated:
            user_ticket: Ticket | None = event.tickets.filter(
                user_id=request.user.id
            ).first()
            if user_ticket is not None:
                schema.status = user_ticket.status()
        return schema
    except Event.DoesNotExist:
        return 404, "Event not found"


@router.get(
    "/{event_id}/attending", response={200: ListType[EventUserInformation], 401: str}
)
def get_users_attending_event(request: AuthenticatedRequest, event_id: int):
    """
    Returns a list of names of the attending users, only if the calling user is staff
    """
    if not request.user.is_staff:
        return 401, "Not a staff user"
    return 200, [
        EventUserInformation(
            full_name=str(ticket.user), food_preferences=ticket.user.food_preferences
        )
        for ticket in Ticket.objects.prefetch_related("user").filter(event_id=event_id)
    ]


@router.get("get-ticket/{event_id}", response={200: UseTicketSchema, 401: str})
def get_event_ticket(request: AuthenticatedRequest, event_id: int):
    """
    Returns a ticket
    """
    tickets: QuerySet[Ticket] = request.user.ticket_set.prefetch_related(
        "event"
    ).filter(event_id=event_id)
    if not tickets.exists():
        return 401, "Unauthorized"
    ticket: Ticket | None = tickets.first()  # Should only be one
    assert ticket is not None, "Should not be possible"
    return UseTicketSchema(uuid=ticket.uuid, event_id=ticket.event.id)


@router.post("use-ticket", response={200: TicketSchema, 401: str, 404: str})
def verify_ticket(request: AuthenticatedRequest, ticket: UseTicketSchema):
    """
    Returns 200 and the ticket schema which will now be used.

    If not a staff user, return 401.

    If the ticket is not found or already used, return 404.
    """
    if not request.user.is_staff:
        return 401, "This route is staff only."
    modified_tickets: int = Ticket.objects.filter(
        uuid=ticket.uuid, event_id=ticket.event_id, used=False
    ).update(used=True)
    if modified_tickets == 1:
        # uuid is unique so we can safely assume we got the ticket
        return 200, Ticket.objects.prefetch_related("user").get(uuid=ticket.uuid)
    return 404, "Ticket not found or already used"


@router.post(
    "acquire-ticket/{event_id}", response={200: EventSchema, 409: str, 404: str}
)
def book_event(request: AuthenticatedRequest, event_id: int):
    """
    Book an event if it is not already fully booked
    """
    with transaction.atomic():
        try:
            event: Event = (
                Event.objects.filter(id=event_id).select_for_update().get(id=event_id)
            )
            if event.release_time is None:
                return 409, "Event release date not yet scheduled"
            if event.release_time >= timezone.now():
                return 409, "Event not yet released"
            if event.end_time <= timezone.now():
                return 409, "Event already ended"
        except Event.DoesNotExist:
            return 404, "Event not found"
        if event.number_booked < event.capacity:
            if event.tickets.filter(user_id=request.user.id).exists():
                return 409, "You have already booked this event"
            ticket: Ticket = Ticket.objects.create(user=request.user, event=event)
            event.number_booked += 1
            event.tickets.add(ticket)
            event.save()

            schema = EventSchema.from_orm(event)
            schema.status = ticket.status()
            return 200, schema
        else:
            return 409, "Event already fully booked"


@router.post(
    "remove-ticket/{event_id}", response={200: EventSchema, 409: str, 404: str}
)
def unbook_event(request: AuthenticatedRequest, event_id: int):
    """
    Unbook an event if you have a ticket.
    """
    with transaction.atomic():
        try:
            event: Event = Event.objects.select_for_update().get(id=event_id)
            if not event.unbook_allowed():
                return 409, "Unbooking period has expired"
        except Event.DoesNotExist:
            return 404, "Event not found"

        # Delete the ticket
        deleted_count, _ = event.tickets.filter(
            user_id=request.user.id, used=False
        ).delete()

        if deleted_count == 0:
            return 404, "You do not have a ticket for this event"

        # Update the counter
        event.number_booked -= 1
        event.save()

        schema = EventSchema.from_orm(event)
        schema.status = EventUserStatus.NOT_BOOKED
        return 200, schema
