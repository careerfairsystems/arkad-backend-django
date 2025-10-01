from django.db import transaction, IntegrityError
from django.db.models import Q
from django.db.models.fields.files import FieldFile
from django.utils import timezone
from pydantic import BaseModel
from pydantic_core import ValidationError
from ninja import File, UploadedFile

from arkad.auth import OPTIONAL_AUTH
from arkad.customized_django_ninja import Router, ListType
from user_models.models import AuthenticatedRequest
from student_sessions.models import (
    StudentSession,
    StudentSessionApplication,
    StudentSessionTimeslot,
)
from student_sessions.schema import (
    TimeslotSchema,
    StudentSessionNormalUserListSchema,
    StudentSessionNormalUserSchema,
    CreateStudentSessionSchema,
    ApplicantSchema,
    StudentSessionApplicationSchema,
    UpdateStudentSessionApplicantStatus,
    StudentSessionApplicationOutSchema,
    ExhibitorTimeslotSchema,
    TimeslotSchemaUser,
)
from user_models.schema import ProfileSchema
from functools import wraps
from typing import Callable, Literal

router = Router(tags=["Student Sessions"])


class AuthenticatedRequestSession(AuthenticatedRequest):
    student_session: StudentSession


def exhibitor_check(func: Callable):
    @wraps(func)
    def wrapper(request: AuthenticatedRequestSession, *args, **kwargs):
        # Saying the request above is a lie, it is still a AuthenticatedRequest when sent into this
        # function. Usure why we get away with it, but it makes the linter believe it is of that type when set on request.

        if not request.user.is_company:
            return 401, "Insufficient permissions"
        try:
            session = StudentSession.objects.get(company_id=request.user.company_id)
        except StudentSession.DoesNotExist:
            return (
                406,
                "Your company does not have a student session, contact your Arkad representative for help",
            )
        request.student_session = session
        return func(request, *args, **kwargs)

    return wrapper


@router.get(
    "/all", response={200: StudentSessionNormalUserListSchema}, auth=OPTIONAL_AUTH
)
def get_student_sessions(request: AuthenticatedRequest):
    """
    Returns a list of available student sessions.

    If the user is authenticated, it will also include their application status for each session.
    """
    sessions: list[StudentSession] = list(
        StudentSession.objects.filter(
            Q(booking_close_time__isnull=True)
            | Q(booking_close_time__gt=timezone.now())
        ).all()
    )
    id_to_session: dict[int, StudentSession] = {s.id: s for s in sessions}
    my_applications_statuses: dict[int, Literal["accepted", "pending", "rejected"]] = (
        dict()
    )
    if request.user.is_authenticated:
        applications = StudentSessionApplication.objects.filter(user=request.user).all()
        for application in applications:
            if application.student_session_id in id_to_session:
                my_applications_statuses[application.student_session_id] = (
                    application.status
                )

    return StudentSessionNormalUserListSchema(
        student_sessions=[
            StudentSessionNormalUserSchema(
                company_id=s.company_id,
                booking_close_time=s.booking_close_time,
                id=s.id,
                available=True,
                user_status=my_applications_statuses.get(s.id, None),
                field_modifications=s.field_modifications,
                description=s.description,
                disclaimer=s.disclaimer,
            )
            for s in sessions
        ],
        numElements=len(sessions),
    )


@router.post("/exhibitor", response={406: str, 201: TimeslotSchema, 401: str})
@exhibitor_check
def create_student_session(
    request: AuthenticatedRequestSession, data: CreateStudentSessionSchema
):
    """
    Creates a student session, user must be an exhibitor.
    """
    session: StudentSession = request.student_session

    time_slot = StudentSessionTimeslot.objects.create(
        start_time=data.start_time,
        duration=data.duration,
        student_session=StudentSession.objects.get(company_id=request.user.company_id),
    )
    session.timeslots.add(time_slot)
    session.save()
    return 201, time_slot


@router.get(
    "/exhibitor/sessions",
    response={200: ListType[ExhibitorTimeslotSchema], 401: str, 406: str},
)
@exhibitor_check
def get_exhibitor_sessions(request: AuthenticatedRequestSession):
    session: StudentSession = request.student_session
    return session.timeslots.prefetch_related("selected", "selected__user").all()


@router.get(
    "/exhibitor/applicants",
    response={200: ListType[ApplicantSchema], 401: str, 404: str},
)
@exhibitor_check
def get_student_session_applicants(request: AuthenticatedRequestSession):
    """
    Returns a list of the applicants to a company's student-session, used when the company wants to select applicants.
    """
    session: StudentSession = request.student_session

    result: list[ApplicantSchema] = []
    applications = (
        StudentSessionApplication.objects.prefetch_related("user")
        .filter(student_session=session)
        .all()
    )
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


@router.post(
    "/exhibitor/update-application-status",
    response={200: str, 409: str, 401: str, 404: str},
)
@exhibitor_check
def update_student_session_application_status(
    request: AuthenticatedRequestSession, data: UpdateStudentSessionApplicantStatus
):
    """
    Used to accept a student for a student session, takes in an applicantUserId.

    This will email the user and allow them to select one of the available timeslots connected to this
    student session.
    """
    session: StudentSession = request.student_session
    try:
        applicant = StudentSessionApplication.objects.get(
            student_session=session, user_id=data.applicant_user_id
        )
        if not applicant.is_pending():
            return 409, "Applicant status has been set and can not be modified"

        match data.status:
            case "accepted":
                applicant.accept()
            case "rejected":
                applicant.deny()
            case _:
                return 409, "Invalid status provided"
    except StudentSessionApplication.DoesNotExist:
        return 404, "Applicant not found"
    return 200, "Applicant accepted"


@router.get(
    "/timeslots",
    response={200: ListType[TimeslotSchemaUser], 401: str, 404: str, 403: str},
)
def get_student_session_timeslots(request: AuthenticatedRequest, company_id: int):
    """
    Returns a list of timeslots for a student session.
    Only viewable if accepted and returns only timeslots which are unbooked or booked by the user.
    """
    try:
        application: StudentSessionApplication = StudentSessionApplication.objects.get(
            user=request.user, student_session__company_id=company_id
        )
        if not application.is_accepted():
            return 403, "You are not accepted to this session"
    except StudentSessionApplication.DoesNotExist:
        return 404, "Application not found"

    timeslots = StudentSessionTimeslot.objects.filter(
        Q(student_session__company_id=company_id)
        & (Q(selected__isnull=True) | Q(selected=application))
    ).all()

    return 200, [
        TimeslotSchemaUser(
            id=timeslot.id,
            start_time=timeslot.start_time,
            duration=timeslot.duration,
            status="bookedByCurrentUser"
            if timeslot.selected == application
            else "free",
        )
        for timeslot in timeslots
    ]


@router.post("/accept", response={200: str, 409: str, 401: str, 404: str})
def confirm_student_session(
    request: AuthenticatedRequest, company_id: int, timeslot_id: int
):
    """
    Accept a timeslot from some student sessions
    """

    try:
        applicant = StudentSessionApplication.objects.get(
            student_session__company_id=company_id, user_id=request.user.id
        )
        if not applicant.is_accepted():
            return 409, "Applicant not accepted"
    except StudentSessionApplication.DoesNotExist:
        return 404, "Application not found"

    try:
        with transaction.atomic():
            timeslot: StudentSessionTimeslot = (
                StudentSessionTimeslot.objects.select_for_update().get(
                    id=timeslot_id, selected=None
                )
            )
            timeslot.selected = applicant
            timeslot.time_booked = timezone.now()
            timeslot.save()
            return 200, "Student session confirmed"
    except IntegrityError:
        # Each application can only be connected to one timeslot
        return 409, "You have already booked a timeslot"
    except StudentSessionTimeslot.DoesNotExist:
        return 404, "Timeslot not found or already taken"


@router.post("/unbook", response={200: str, 401: str, 404: str})
def unbook_student_session(request: AuthenticatedRequest, company_id: int):
    """
    Unbook a timeslot from some student sessions
    """

    try:
        application = StudentSessionApplication.objects.get(
            student_session__company_id=company_id, user_id=request.user.id
        )
        if not application.is_accepted():
            return 409, "Applicant not accepted"
    except StudentSessionApplication.DoesNotExist:
        return 404, "Application not found"

    try:
        timeslot: StudentSessionTimeslot = StudentSessionTimeslot.objects.get(
            selected=application
        )
        timeslot.selected = None
        timeslot.time_booked = None
        timeslot.save()
        return 200, "Student session unbooked"
    except StudentSessionTimeslot.DoesNotExist:
        return 404, "Timeslot not found or already taken"


@router.post("/apply", response={404: str, 409: str, 200: str})
def apply_for_session(
    request: AuthenticatedRequest, data: StudentSessionApplicationSchema
):
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
            company_id=data.company_id, booking_close_time__gte=timezone.now()
        )
    except StudentSession.DoesNotExist:
        return 404, "Session not found, or booking has closed"

    request.user.programme = data.programme
    request.user.linkedin = data.linkedin
    request.user.master_title = data.master_title
    request.user.study_year = data.study_year
    request.user.save()

    try:
        StudentSessionApplication.objects.create(
            user=request.user,
            student_session=session,
            motivation_text=data.motivation_text,
        )
    except IntegrityError:
        return 409, "You have already applied to this session"

    return 200, "You have now applied to the session"


@router.post("cv", response={200: str, 404: str})
def update_cv_for_session(
    request: AuthenticatedRequest, company_id: int, cv: UploadedFile = File(...)
):  # type: ignore[type-arg]
    """
    Sets the CV for the user for some companies student sessions.
    """

    try:
        application: StudentSessionApplication = StudentSessionApplication.objects.get(
            user_id=request.user.id, student_session__company_id=company_id
        )
    except StudentSessionApplication.DoesNotExist:
        return 404, "Application not found"
    application.cv = cv
    application.save()
    return 200, "CV updated"


@router.get(
    "/application", response={200: StudentSessionApplicationOutSchema, 404: str}
)
def get_student_session_application(request: AuthenticatedRequest, company_id: int):
    """
    Returns the motivation text for the current user.

    If one does not exist or is explicitly None, None is returned
    """
    try:
        application = StudentSessionApplication.objects.get(user=request.user)
        return 200, StudentSessionApplicationOutSchema(
            motivation_text=application.motivation_text,
            cv=application.cv.url
            if application.cv
            else (request.user.cv.url if request.user.cv else None),
            company_id=company_id,
        )
    except StudentSessionApplication.DoesNotExist:
        return 404, "Application not found"
