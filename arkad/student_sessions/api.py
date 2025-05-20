import logging

from django.db import transaction, IntegrityError
from django.db.models.fields.files import FieldFile
from django.utils import timezone
from pydantic import BaseModel
from pydantic_core import ValidationError

from arkad.customized_django_ninja import Router
from user_models.models import AuthenticatedRequest
from student_sessions.models import (
    StudentSession,
    StudentSessionApplication,
    StudentSessionTimeslot
)
from student_sessions.schema import (
    TimeslotSchema,
    StudentSessionNormalUserListSchema,
    StudentSessionNormalUserSchema,
    CreateStudentSessionSchema,
    ApplicantSchema,
    StudentSessionApplicationSchema,
)
from user_models.schema import ProfileSchema

router = Router(tags=["Student Sessions"])

def exhibitor_check(request: AuthenticatedRequest) -> tuple[StudentSession | None, tuple[int, str] | None]:
    if not request.user.is_company:
        return None, (401, "Insufficient permissions")
    try:
        return StudentSession.objects.get(company_id=request.user.company_id), None
    except StudentSession.DoesNotExist:
        return None, (406, "Your company does not have a student session, contact your Arkad representative for help")



@router.get("/all", response={200: StudentSessionNormalUserListSchema}, auth=None)
def get_student_sessions(request: AuthenticatedRequest):
    """
    Returns a list of available student sessions.
    """
    sessions: list[StudentSession] = list(StudentSession.objects.all())

    return StudentSessionNormalUserListSchema(
        student_sessions=[
            StudentSessionNormalUserSchema(
                company_id=s.company_id,
                booking_close_time=s.booking_close_time,
                id=s.id,
                available=s.booking_close_time > timezone.now() if s.booking_close_time else True,
            )
            for s in sessions
        ],
        numElements=len(sessions),
    )


@router.post("/exhibitor", response={406: str, 201: TimeslotSchema, 401: str})
def create_student_session(request: AuthenticatedRequest, data: CreateStudentSessionSchema):
    """
    Creates a student session, user must be an exhibitor.
    """
    session: StudentSession | None
    error: tuple[int, str] | None
    session, error = exhibitor_check(request)
    if error is not None:
        return error

    time_slot = StudentSessionTimeslot.objects.create(
        start_time=data.start_time,
        duration=data.duration,
    )
    session.timeslots.add(time_slot)
    session.save()
    return 201, time_slot


@router.get("/exhibitor/sessions", response={200: list[TimeslotSchema], 401: str, 406: str})
def get_exhibitor_sessions(request: AuthenticatedRequest):
    session: StudentSession | None
    error: tuple[int, str] | None
    session, error = exhibitor_check(request)
    if error is not None:
        return error
    return session.timeslots.prefetch_related("selected").all()


@router.get(
    "/exhibitor/applicants", response={200: list[ApplicantSchema], 401: str, 404: str}
)
def get_applicants(request: AuthenticatedRequest):
    """
    Returns a list of the applicants to a company's student-session, used when the company wants to select applicants.
    """
    session: StudentSession | None
    error: tuple[int, str] | None
    session, error = exhibitor_check(request)
    if error is not None:
        return error

    result: list[ApplicantSchema] = []
    applications = StudentSessionApplication.objects.prefetch_related("user").filter(student_session=session).all()
    for a in applications:
        cv: FieldFile | None = a.cv or a.user.cv
        result.append(
            ApplicantSchema(
                user=ProfileSchema.from_orm(a.user),
                motivation_text=a.motivation_text,
                cv=cv.url if cv else None,
            )
        )
    return 200, result


@router.post("/exhibitor/accept", response={200: str, 409: str, 401: str, 404: str})
def accept_student_session(
    request: AuthenticatedRequest, applicant_user_id: int
):
    """
    Used to accept a student for a student session, takes in an applicant_user_id.

    This will email the user and allow them to select one of the available timeslots connected to this
    student session.
    """
    session: StudentSession | None
    error: tuple[int, str] | None
    session, error = exhibitor_check(request)
    if error is not None:
        return error
    try:
        applicant = StudentSessionApplication.objects.get(student_session=session, user_id=applicant_user_id)
        applicant.accept()  # Sends
    except StudentSessionApplication.DoesNotExist:
        return 404, "Applicant not found"
    return 200, "Applicant accepted"

@router.get("/timeslots", response={200: list[TimeslotSchema], 401: str, 404: str})
def get_student_session_timeslots(request: AuthenticatedRequest, session_id: int):
    """
    Returns a list of timeslots for a student session.
    Only viewable if accepted
    """
    try:
        application: StudentSessionApplication = StudentSessionApplication.objects.get(user=request.user, student_session_id=session_id)
        if not application.is_accepted():
            return 401, "You are not accepted to this session"
    except StudentSessionApplication.DoesNotExist:
        return 404, "Application not found"


    timeslots = StudentSessionTimeslot.objects.filter(student_session_id=session_id).all()

    return 200, [
        TimeslotSchema(
            id=timeslot.id,
            start_time=timeslot.start_time,
            duration=timeslot.duration,
            selected=ApplicantSchema.from_orm(timeslot.selected) if timeslot.selected else None,
        )
        for timeslot in timeslots
    ]

@router.post("/accept", response={200: str, 409: str, 401: str, 404: str})
def confirm_student_session(
        request: AuthenticatedRequest, session_id: int, timeslot_id: int
):
    """
    Accept a timeslot from some student sessions
    """

    try:
        applicant = StudentSessionApplication.objects.get(student_session_id=session_id, user_id=request.user.id)
        if not applicant.is_accepted():
            return 409, "Applicant not accepted"
    except StudentSessionApplication.DoesNotExist:
        return 404, "Application not found"

    try:
        with transaction.atomic():
            timeslot: StudentSessionTimeslot = StudentSessionTimeslot.objects.select_for_update().get(id=timeslot_id, selected=None)
            timeslot.selected = applicant
            timeslot.time_booked = timezone.now()
            timeslot.save()
            return 200, "Student session confirmed"
    except StudentSessionTimeslot.DoesNotExist:
        return 404, "Timeslot not found or already taken"

@router.post("/unbook", response={200: str, 401: str, 404: str})
def unbook_student_session(request: AuthenticatedRequest, session_id: int):
    """
    Unbook a timeslot from some student sessions
    """

    try:
        application = StudentSessionApplication.objects.get(student_session_id=session_id, user_id=request.user.id)
        if not application.is_accepted():
            return 409, "Applicant not accepted"
    except StudentSessionApplication.DoesNotExist:
        return 404, "Application not found"

    try:
        timeslot: StudentSessionTimeslot = StudentSessionTimeslot.objects.get(selected=application)
        timeslot.selected = None
        timeslot.time_booked = None
        timeslot.save()
        return 200, "Student session unbooked"
    except StudentSessionTimeslot.DoesNotExist:
        return 404, "Timeslot not found or already taken"

@router.post("/apply", response={404: str, 409: str, 200: str})
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

    try:
        session: StudentSession = StudentSession.objects.get(
            id=data.session_id, booking_close_time__gte=timezone.now()
        )
    except StudentSession.DoesNotExist:
        return 404, "Session not found, or booking has closed"

    if data.update_profile:
        request.user.programme = data.programme
        request.user.linkedin = data.linkedin
        request.user.master_title = data.master_title
        request.user.study_year = data.study_year
        request.user.save()

    try:
        StudentSessionApplication.objects.create(
            user=request.user,
            company=session.company,
            student_session=session,
            motivation_text=data.motivation_text,
            cv=data.cv,
        )
    except IntegrityError as e:
        logging.exception(e)
        return 409, "You have already applied to this session"

    return 200, "You have now applied to the session"

@router.get("/application", response={200: StudentSessionApplicationSchema | None})
def get_student_session_application(request: AuthenticatedRequest, company_id: int):
    """
    Returns the motivation text for the current user.

    If one does not exist or is explicitly None, None is returned
    """
    try:
        application = StudentSessionApplication.objects.get(user=request.user, company_id=company_id)
        return 200, StudentSessionApplicationSchema(
            motivation_text=application.motivation_text,
            cv=application.cv.url if application.cv else (request.user.cv.url if request.user.cv else None),
            session_id=application.student_session_id
        )
    except StudentSessionApplication.DoesNotExist:
        return 200, None
