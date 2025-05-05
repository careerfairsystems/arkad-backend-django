from django.db import transaction
from django.http import HttpRequest
from pydantic import BaseModel
from pydantic_core import ValidationError

from arkad import Router
from user_models.models import AuthenticatedRequest
from student_sessions.models import (
    StudentSession,
    StudentSessionApplication,
    CompanyStudentSessionMotivation,
)
from student_sessions.schema import (
    StudentSessionSchema,
    StudentSessionNormalUserListSchema,
    StudentSessionNormalUserSchema,
    CreateStudentSessionSchema,
    ApplicantSchema,
    StudentSessionApplicationSchema, MotivationTextUpdateSchema,
)
from companies.models import Company
from user_models.schema import ProfileSchema

router = Router(tags=["Student Sessions"])


@router.get("/all", response={200: StudentSessionNormalUserListSchema})
def get_student_sessions(request: AuthenticatedRequest, only_available_sessions: bool = False):
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
        student_sessions=[
            StudentSessionNormalUserSchema(
                start_time=s.start_time,
                duration=s.duration,
                company_id=s.company_id,
                booking_close_time=s.booking_close_time,
                id=s.id,
                available=s.interviewee is None,
            )
            for s in sessions
        ],
        numElements=len(sessions),
    )


@router.post("/exhibitor", response={406: str, 201: StudentSessionSchema, 401: str})
def create_student_session(request: AuthenticatedRequest, session: CreateStudentSessionSchema):
    """
    Creates a student session, user must be an exhibitor.
    """
    company_id: int = session.company_id
    if request.user.is_company_admin(company_id):
        try:
            return 201, StudentSession.objects.create(
                company=Company.objects.get(id=company_id),
                start_time=session.start_time,
                duration=session.duration,
                booking_close_time=session.booking_close_time,
            )
        except Company.DoesNotExist:
            return 406, "Company not found"
    return 401, "Insufficient permissions"


@router.get("/exhibitor/sessions", response={200: list[StudentSessionSchema], 401: str})
def get_exhibitor_sessions(request: AuthenticatedRequest):
    if not request.user.is_company:
        return 401, "Insufficient permissions"
    return StudentSession.objects.filter(company=request.user.company).prefetch_related(
        "interviewee"
    )


@router.get(
    "/exhibitor/applicants", response={200: list[ApplicantSchema], 401: str, 404: str}
)
def get_applicants(request: AuthenticatedRequest, session_id: int):
    """
    Returns a list of the applicants to a company's student-session, used when the company wants to select applicants.
    """
    try:
        session: StudentSession = StudentSession.objects.get(id=session_id)
    except StudentSession.DoesNotExist:
        return 404, "Student session not found"

    if not request.user.is_company_admin(session.company_id):
        return 401, "Insufficient permissions"
    return 200, [
        ApplicantSchema(
            user=ProfileSchema.from_orm(a.motivation.user),
            motivation_text=a.motivation.motivation_text,
        )
        for a in session.applications.prefetch_related("motivation").all()
    ]


@router.post("/exhibitor/accept", response={200: str, 409: str, 401: str, 404: str})
def accept_student_session(
    request: AuthenticatedRequest, session_id: int, applicant_user_id: int
):
    """
    Used to accept a student for a student session, takes in a session_id and an applicant_user_id.
    """
    with transaction.atomic():
        try:
            session: StudentSession = StudentSession.objects.select_for_update().get(
                id=session_id, interviewee=None
            )
        except StudentSession.DoesNotExist:
            return (
                404,
                "Either this timeslot does not exist or an applicant has already been accepted",
            )

        if not request.user.is_company_admin(session.company_id):
            return 401, "Insufficient permissions"

        session.interviewee_id = applicant_user_id
        session.save()

        # Remove this interviewee from the rest of the company's lists
        assert request.user.company is not None, "Should not be possible to be None"
        for s in StudentSession.objects.filter(
            company_id=request.user.company.id,
            applications__motivation__user__id=applicant_user_id,
        ):
            s.applications.filter(motivation__user=applicant_user_id).delete()
            s.save()
        return 200, "Accepted user"


@router.post("/apply", response={404: str, 409: str, 200: StudentSessionSchema})
def apply_for_session(request: AuthenticatedRequest, data: StudentSessionApplicationSchema):
    """
    Used to apply to a student session, takes in the session id and signs up the current user.
    """

    class UserRequirements(BaseModel):
        first_name: str
        last_name: str

    try:
        UserRequirements(
            first_name=request.user.first_name, last_name=request.user.last_name
        )
    except ValidationError as e:
        return 409, str(e.errors())

    with transaction.atomic():
        try:
            session: StudentSession = StudentSession.objects.select_for_update().get(
                id=data.session_id, interviewee=None
            )
        except StudentSession.DoesNotExist:
            return 404, "Session not found or already booked"

        # User already has a booked session with the same company
        if StudentSession.objects.filter(
            interviewee_id=request.user.id, company_id=session.company_id
        ).exists():
            return 409, "User already booked"

        motivation = CompanyStudentSessionMotivation.objects.get_or_create(
            user=request.user, company=session.company
        )[0]
        if data.motivation_text is not None:
            motivation.motivation_text = data.motivation_text
            motivation.save()
        application: StudentSessionApplication = (
            StudentSessionApplication.objects.create(motivation=motivation)
        )
        session.applications.add(application)
        session.save()
    return 200, session

@router.get("/motivation", response={200: str | None})
def get_student_session_motivation(request: AuthenticatedRequest, company_id: int):
    """
    Returns the motivation text for the current user.

    If one does not exist or is explicitly None, None is returned
    """
    try:
        motivation = CompanyStudentSessionMotivation.objects.get(user=request.user, company_id=company_id)
        return 200, motivation.motivation_text
    except CompanyStudentSessionMotivation.DoesNotExist:
        return 200, None


@router.put("/motivation", response={200: str | None})
def update_student_session_motivation(request: AuthenticatedRequest, data: MotivationTextUpdateSchema):
    """
    Updates the motivation text for the current user.

    If one does not exist, it is created
    """
    try:
        motivation = CompanyStudentSessionMotivation.objects.get(user=request.user, company_id=data.company_id)
        motivation.motivation_text = data.motivation_text
        motivation.save()
        return 200, motivation.motivation_text
    except CompanyStudentSessionMotivation.DoesNotExist:
        motivation = CompanyStudentSessionMotivation.objects.create(user=request.user,
                                                                    company_id=data.company_id,
                                                                    motivation_text=data.motivation_text)
        return 200, motivation.motivation_text

@router.delete("/motivation", response={200: str, 404: str})
def delete_student_session_motivation(request: AuthenticatedRequest, company_id: int):
    """
    Deletes the motivation text for the current user.

    If one does not exist, a 404 is returned
    """
    try:
        motivation = CompanyStudentSessionMotivation.objects.get(user=request.user, company_id=company_id)
        motivation.delete()
        return 200, "Deleted motivation text"
    except CompanyStudentSessionMotivation.DoesNotExist:
        return 404, "Motivation text does not exist"