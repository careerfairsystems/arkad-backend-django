from django.http import HttpRequest
from ninja import Router

from student_sessions.models import StudentSession
from student_sessions.schema import StudentSessionListSchema, StudentSessionSchema, AvailableStudentSessionListSchema, \
    AvailableStudentSessionSchema, CreateStudentSessionSchema
from user_models.models import Company

router = Router()

@router.get("/available", response={200: AvailableStudentSessionListSchema})
def get_available_student_sessions(request: HttpRequest):
    sessions: list = list(StudentSession.available_sessions())
    return AvailableStudentSessionListSchema(
        student_sessions=[AvailableStudentSessionSchema.from_orm(s) for s in sessions],
        numElements=len(sessions))

@router.post("/create-student-session", response={406: str, 201: StudentSessionSchema})
def create_student_session(request: HttpRequest, session: CreateStudentSessionSchema):
    data: dict = session.model_dump()
    try:
        data["company"] = Company.objects.get(id=data.pop("company_id"))
    except Company.DoesNotExist:
        return 406, "Company not found"
    return 201, StudentSession.objects.create(**data)
