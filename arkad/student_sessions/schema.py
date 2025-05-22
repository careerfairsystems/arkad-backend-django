from datetime import datetime
from typing import List, Optional
from arkad.customized_django_ninja import Schema
from user_models.schema import ProfileSchema


class StudentSessionApplicationSchema(Schema):
    cv: str | None = None
    profile_picture: str | None = None
    programme: str | None = None
    linkedin: str | None = None
    master_title: str | None = None
    study_year: int | None = None
    motivation_text: str | None = None
    update_profile: bool | None = None
    company_id: int


class ApplicantSchema(Schema):
    user: ProfileSchema
    cv: str | None = None
    motivation_text: str


class TimeslotSchema(Schema):
    start_time: datetime
    duration: int
    selected: Optional[StudentSessionApplicationSchema] = None
    id: int


class CreateStudentSessionSchema(Schema):
    start_time: datetime
    duration: int
    booking_close_time: datetime


class StudentSessionListSchema(Schema):
    student_sessions: List[TimeslotSchema]
    numElements: int


class StudentSessionNormalUserSchema(Schema):
    company_id: int
    booking_close_time: datetime | None
    available: bool
    id: int


class StudentSessionNormalUserListSchema(Schema):
    student_sessions: List[StudentSessionNormalUserSchema]
    numElements: int


class MotivationTextUpdateSchema(Schema):
    motivation_text: str | None
    company_id: int
