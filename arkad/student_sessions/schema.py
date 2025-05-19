from datetime import datetime
from typing import List, Optional
from arkad.customized_django_ninja import Schema
from user_models.schema import ProfileSchema


class StudentSessionSchema(Schema):
    start_time: datetime
    duration: int
    interviewee: Optional[ProfileSchema] = None
    booking_close_time: datetime
    id: int


class CreateStudentSessionSchema(Schema):
    start_time: datetime
    duration: int
    booking_close_time: datetime


class StudentSessionListSchema(Schema):
    student_sessions: List[StudentSessionSchema]
    numElements: int


class StudentSessionNormalUserSchema(Schema):
    start_time: datetime
    duration: int
    company_id: int
    booking_close_time: datetime | None
    available: bool
    id: int


class StudentSessionNormalUserListSchema(Schema):
    student_sessions: List[StudentSessionNormalUserSchema]
    numElements: int


class ApplicantSchema(Schema):
    user: ProfileSchema
    motivation_text: str


class StudentSessionApplicationSchema(Schema):
    class ProfileSchema(Schema):
        # If update_profile update user data
        # Keep this separate per application otherwise or both cases.
        cv: str | None = None
        profile_picture: str | None = None
        programme: str | None = None
        linkedin: str | None = None
        master_title: str | None = None
        study_year: int | None = None
        update_profile: bool



    motivation_text: str | None = None
    session_id: int

class MotivationTextUpdateSchema(Schema):
    motivation_text: str | None
    company_id: int
