
from django.db import transaction
from django.http import HttpRequest
from ninja import Router

from student_sessions.models import StudentSession
from student_sessions.schema import (
    StudentSessionSchema,
    StudentSessionNormalUserListSchema,
    StudentSessionNormalUserSchema,
    CreateStudentSessionSchema,
)
from companies.models import Company
from user_models.schema import ProfileSchema

router = Router(tags=["Student Sessions"])


@router.get("/all", response={200: StudentSessionNormalUserListSchema})
def get_student_sessions(request: HttpRequest, only_available_sessions: bool = False):
    """
    Returns a list of available student sessions.

    Set only_available_sessions to True to only return available sessions.
    """
    sessions: list[StudentSession]
    if only_available_sessions:
        sessions = list(StudentSession.available_sessions())
    else:
        sessions = list(StudentSession.objects.all())

    return StudentSessionNormalUserListSchema(
        student_sessions=[StudentSessionNormalUserSchema(
            start_time=s.start_time,
            duration=s.duration,
            company_id=s.company_id,
            booking_close_time=s.booking_close_time,
            id=s.id,
            available=s.interviewee is None
        ) for s in sessions],
        numElements=len(sessions),
    )


@router.post("/exhibitor", response={406: str, 201: StudentSessionSchema, 401: str})
def create_student_session(request: HttpRequest, session: CreateStudentSessionSchema):
    """
    Creates a student session, user must be an exhibitor.
    """
    data: dict = session.model_dump()
    company_id: int = data.pop("company_id")
    if request.user.is_company_admin(company_id):
        try:
            data["company"] = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return 406, "Company not found"
        return 201, StudentSession.objects.create(**data)
    return 401, "Insufficient permissions"

@router.get("/exhibitor/sessions", response={200: list[StudentSessionSchema], 401: str})
def get_exhibitor_sessions(request: HttpRequest):
    if not request.user.is_company:
        return 401, "Insufficient permissions"
    return StudentSession.objects.filter(company=request.user.company).prefetch_related("interviewee")


@router.get("/exhibitor/applicants", response={200: list[ProfileSchema], 401: str, 404: str})
def get_applicants(request: HttpRequest, session_id: int):
    """
    Returns a list of the applicants to a company's student-session, used when the company wants to select applicants.
    """
    try:
        session: StudentSession = StudentSession.objects.get(id=session_id)
    except StudentSession.DoesNotExist:
        return 404, "Student session not found"

    if not request.user.is_company_admin(session.company_id):
        return 401, "Insufficient permissions"
    return 200, session.applicants

@router.post("/exhibitor/accept", response={200: str, 409: str, 401: str, 404: str})
def accept_student_session(request: HttpRequest, session_id: int, applicant_user_id: int):
    """
    Used to accept a student for a student session, takes in a session_id and an applicant_user_id.
    """
    with transaction.atomic():
        try:
            session: StudentSession = StudentSession.objects.select_for_update().get(id=session_id, interviewee=None)
        except StudentSession.DoesNotExist:
            return 404, "Either this timeslot does not exist or an applicant has already been accepted"

        if not request.user.is_company_admin(session.company_id):
            return 401, "Insufficient permissions"

        session.interviewee_id = applicant_user_id
        session.save()

        # Remove this interviewee from the rest of the company's lists

        for s in  StudentSession.objects.filter(company_id=request.user.company.id,
                                                applicants__id__contains=applicant_user_id):
            s.applicants.remove(applicant_user_id)
            s.save()

        return 200, "Accepted user"

@router.post("/apply", response={404: str, 409: str, 200: StudentSessionSchema})
def apply_for_session(request: HttpRequest, session_id: int):
    """
    Used to apply to a student session, takes in the session id and signs up the current user.
    """
    with transaction.atomic():
        try:
            session: StudentSession = StudentSession.objects.select_for_update().get(
                id=session_id, interviewee=None
            )
        except StudentSession.DoesNotExist:
            return 404, "Session not found or already booked"

        # User already has a booked session with the same company
        if StudentSession.objects.filter(interviewee_id=request.user.id, company_id=session.company_id).exists():
            return 409, "User already booked"

        session.applicants.add(request.user)
        session.save()
    return 200, session
