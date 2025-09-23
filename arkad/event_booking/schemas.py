from datetime import datetime
from uuid import UUID
from arkad.customized_django_ninja import Schema


class EventSchema(Schema):
    id: int
    name: str
    description: str
    type: str
    location: str
    language: str
    start_time: datetime
    end_time: datetime
    capacity: int
    number_booked: int
    company_id: int | None


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
    full_name: str
    food_preferences: str | None
