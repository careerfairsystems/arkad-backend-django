from django.http import HttpRequest
from ninja import Router

from student_sessions.models import StudentSession
from student_sessions.schema import StudentSessionListSchema, StudentSessionSchema, AvailableStudentSessionListSchema, \
    AvailableStudentSessionSchema

router = Router()

@router.get("/available", response={200: AvailableStudentSessionListSchema})
def get_available_student_sessions(request: HttpRequest):
    sessions: list = list(StudentSession.available_sessions())
    return AvailableStudentSessionListSchema(
        student_sessions=[AvailableStudentSessionSchema.from_orm(s) for s in sessions],
        numElements=len(sessions))
