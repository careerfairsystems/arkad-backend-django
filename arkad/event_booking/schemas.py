from datetime import datetime
from enum import Enum
from typing import Type, Any
from uuid import UUID

from ninja.schema import S

from arkad.customized_django_ninja import Schema


class EventUserStatus(str, Enum):
    NOT_BOOKED = "not_booked"
    BOOKED = "booked"
    TICKET_USED = "ticket_used"


class EventSchema(Schema):
    id: int
    name: str
    description: str
    type: str
    location: str
    language: str
    release_time: datetime | None
    start_time: datetime
    end_time: datetime

    booking_freezes_at: datetime
    capacity: int
    number_booked: int
    company_id: int | None
    status: EventUserStatus  # This field is not in the ORM model, but is set manually, default is NOT_BOOKED

    @classmethod
    def from_orm(cls: Type[S], obj: Any, **kw: Any) -> S:
        if "status" not in kw:
            setattr(obj, "status", EventUserStatus.NOT_BOOKED)
        return super().from_orm(obj, **kw)


class UserEventInformationSchema(Schema):
    id: int
    first_name: str | None
    last_name: str | None
    food_preferences: str | None


class TicketSchema(Schema):
    user: UserEventInformationSchema
    uuid: UUID
    event_id: int
    used: bool


class UseTicketSchema(Schema):
    uuid: UUID
    event_id: int


class EventUserInformation(Schema):
    user_id: int
    full_name: str
    food_preferences: str | None
    ticket_used: bool
