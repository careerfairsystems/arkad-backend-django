from datetime import datetime
from typing import List, Optional

from ninja import Schema

from user_models.schema import ProfileSchema


class StudentSessionSchema(Schema):
    start_time: datetime
    duration: int
    company_id: int
    interviewee: Optional[ProfileSchema] = None
    booking_close_time: datetime
    id: int
    applicants: List[ProfileSchema]


class CreateStudentSessionSchema(Schema):
    start_time: datetime
    duration: int
    booking_close_time: datetime
    company_id: int


class StudentSessionListSchema(Schema):
    student_sessions: List[StudentSessionSchema]
    numElements: int


class AvailableStudentSessionSchema(Schema):
    start_time: datetime
    duration: int
    company_id: int
    booking_close_time: datetime
    id: int


class AvailableStudentSessionListSchema(Schema):
    student_sessions: List[AvailableStudentSessionSchema]
    numElements: int
