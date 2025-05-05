from datetime import datetime
from uuid import UUID
from arkad import Schema


class EventSchema(Schema):
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


class TicketSchema(Schema):
    user_id: int
    uuid: UUID
    event_id: int
    used: bool


class UseTicketSchema(Schema):
    uuid: UUID


class EventUserInformation(Schema):
    full_name: str
    food_preferences: str | None
