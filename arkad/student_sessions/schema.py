from ninja import ModelSchema, Schema

from student_sessions.models import StudentSession
from user_models.schema import ProfileSchema, CompanySchema


class StudentSessionSchema(ModelSchema):
    interviewee: ProfileSchema
    company: CompanySchema

    class Meta:
        model = StudentSession
        fields = ("start_time", "duration", "company", "interviewee", "booking_close_time")

class StudentSessionListSchema(Schema):
    student_sessions: list[StudentSessionSchema]
    numElements: int

class AvailableStudentSessionSchema(ModelSchema):
    company: CompanySchema

    class Meta:
        model = StudentSession
        fields = ("start_time", "duration", "company", "booking_close_time")

class AvailableStudentSessionListSchema(Schema):
    student_sessions: list[AvailableStudentSessionSchema]
    numElements: int
