from datetime import datetime
from typing import List, Literal
from arkad.customized_django_ninja import Schema
from user_models.schema import ProfileSchema


class StudentSessionApplicationSchema(Schema):
    programme: str | None = None
    linkedin: str | None = None
    master_title: str | None = None
    study_year: int | None = None
    motivation_text: str | None = None
    update_profile: bool | None = None
    company_id: int


class StudentSessionApplicationOutSchema(Schema):
    motivation_text: str | None = None
    cv: str | None = None
    company_id: int


class ApplicantSchema(Schema):
    user: ProfileSchema
    cv: str | None = None
    motivation_text: str


class TimeslotSchema(Schema):
    start_time: datetime
    duration: int
    id: int


class CreateStudentSessionSchema(Schema):
    start_time: datetime
    duration: int
    booking_close_time: datetime


class StudentSessionNormalUserSchema(Schema):
    company_id: int
    booking_close_time: datetime | None
    available: bool
    user_status: Literal["accepted", "rejected", "pending"] | None = None
    id: int


class StudentSessionNormalUserListSchema(Schema):
    student_sessions: List[StudentSessionNormalUserSchema]
    numElements: int


class MotivationTextUpdateSchema(Schema):
    motivation_text: str | None
    company_id: int


class UpdateStudentSessionApplicantStatus(Schema):
    applicant_user_id: int
    status: Literal["accepted", "rejected"]
