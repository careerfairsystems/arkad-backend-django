from datetime import datetime
from typing import List, Literal
from arkad.customized_django_ninja import Schema
from student_sessions.dynamic_fields import FieldModificationSchema
from user_models.schema import ProfileSchema


class StudentSessionApplicationSchema(Schema):
    programme: str | None = None
    linkedin: str | None = None
    master_title: str | None = None
    study_year: int | None = None
    motivation_text: str | None = None
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


class TimeslotSchemaUser(TimeslotSchema):
    status: Literal["free", "bookedByCurrentUser"]


class StudentSessionApplicationSchemaAccepted(Schema):
    id: int
    user: ProfileSchema
    motivation_text: str | None = None
    cv: str | None = None
    status: Literal["accepted", "rejected", "pending"]
    timestamp: datetime | None = None


class ExhibitorTimeslotSchema(TimeslotSchema):
    selected: StudentSessionApplicationSchemaAccepted | None = None


class CreateStudentSessionSchema(Schema):
    start_time: datetime
    duration: int
    booking_close_time: datetime


class StudentSessionNormalUserSchema(Schema):
    company_id: int
    booking_close_time: datetime | None
    available: bool
    user_status: Literal["accepted", "rejected", "pending"] | None = None
    description: str | None
    disclaimer: str | None
    field_modifications: list[FieldModificationSchema]
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
