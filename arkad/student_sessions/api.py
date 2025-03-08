import logging

from django.db import transaction, IntegrityError
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
from user_models.schema import ProfileSchema

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
    if request.user.is_company_admin(company_id):
        try:
            data["company"] = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return 406, "Company not found"
        return 201, StudentSession.objects.create(**data)
    return 401, "Insufficient permissions"

@router.get("/applicants", response={200: list[ProfileSchema], 401: str, 404: str})
def get_applicants(request: HttpRequest, session_id: int):
    try:
        session: StudentSession = StudentSession.objects.get(id=session_id)
    except StudentSession.DoesNotExist:
        return 404, "Student session not found"

    if not request.user.is_company_admin(session.company_id):
        return 401, "Insufficient permissions"
    return 200, session.applicants

@router.post("/accept", response={200: str, 409: str, 401: str, 404: str})
def accept_student_session(request: HttpRequest, session_id: int, applicant_user_id: int):
    with transaction.atomic():
        try:
            session: StudentSession = StudentSession.objects.select_for_update().get(id=session_id, interviewee=None)
        except StudentSession.DoesNotExist:
            return 404, "Either this timeslot does not exist or an applicant has already been accepted"

        if not request.user.is_company_admin(session.company_id):
            return 401, "Insufficient permissions"

        session.interviewee_id = applicant_user_id
        session.save()
        return 200, "Accepted user"

@router.post("/apply", response={404: str, 409: str, 201: StudentSessionSchema})
def apply_for_session(request: HttpRequest, session_id: int):
    with transaction.atomic():
        try:
            session: StudentSession = StudentSession.objects.select_for_update().get(
                id=session_id, interviewee=None
            )
        except StudentSession.DoesNotExist:
            return 404, "Session not found or already booked"
        except IntegrityError as e:
            logging.error(e)
            return 409, "You may only have one session per company"
        session.applicants.add(request.user)
        session.save()
    return 201, session
