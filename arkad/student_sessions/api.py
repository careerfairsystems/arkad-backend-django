from django.db import transaction
from django.http import HttpRequest
from ninja import Router

from student_sessions.models import StudentSession
from student_sessions.schema import (
    StudentSessionSchema,
    AvailableStudentSessionListSchema,
    AvailableStudentSessionSchema,
    CreateStudentSessionSchema,
)
from companies.models import Company

router = Router(tags=["Student Sessions"])


@router.get("/available", response={200: AvailableStudentSessionListSchema})
def get_available_student_sessions(request: HttpRequest):
    sessions: list = list(StudentSession.available_sessions())
    return AvailableStudentSessionListSchema(
        student_sessions=[AvailableStudentSessionSchema.from_orm(s) for s in sessions],
        numElements=len(sessions),
    )


@router.post("/", response={406: str, 201: StudentSessionSchema, 401: str})
def create_student_session(request: HttpRequest, session: CreateStudentSessionSchema):
    data: dict = session.model_dump()
    company_id: int = data.pop("company_id")
    if request.user.is_company and request.user.company_id == company_id:
        try:
            data["company"] = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return 406, "Company not found"
        return 201, StudentSession.objects.create(**data)
    return 401, "Insufficient permissions"


@router.post("/book", response={406: str, 201: StudentSessionSchema})
def book_session(request: HttpRequest, session_id: int):
    with transaction.atomic():
        try:
            session: StudentSession = StudentSession.objects.select_for_update().get(
                id=session_id, interviewee=None
            )
        except StudentSession.DoesNotExist:
            return 406, "Session not found or already booked"

        session.interviewee = request.user
        session.save()

    return 201, session
