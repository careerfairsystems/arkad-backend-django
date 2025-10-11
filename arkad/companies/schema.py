from typing import List, Optional

from arkad.customized_django_ninja import Schema


class JobSchema(Schema):
    id: int
    link: Optional[str] = None
    description: Optional[str] = None
    location: List[str] = []
    job_type: List[str] = []
    title: Optional[str] = None


class CompanyUpdate(Schema):
    name: Optional[str] = None
    description: Optional[str] = None
    did_you_know: Optional[str] = None
    logo_url: Optional[str] = None
    url_linkedin: Optional[str] = None
    url_instagram: Optional[str] = None
    url_facebook: Optional[str] = None
    url_twitter: Optional[str] = None
    url_youtube: Optional[str] = None
    website: Optional[str] = None
    company_name: Optional[str] = None
    company_email: Optional[str] = None
    company_phone: Optional[str] = None
    student_session_motivation: Optional[str] = None
    days_with_studentsession: Optional[int] = None
    desired_degrees: Optional[List[str]] = None
    desired_programme: Optional[List[str]] = None
    desired_competences: Optional[List[str]] = None
    positions: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    employees_locally: Optional[int] = None
    employees_globally: Optional[int] = None


class CompanyOut(Schema):
    id: int
    name: str
    description: Optional[str] = None
    did_you_know: Optional[str] = None
    logo_url: Optional[str] = None
    url_linkedin: Optional[str] = None
    url_instagram: Optional[str] = None
    url_facebook: Optional[str] = None
    url_twitter: Optional[str] = None
    url_youtube: Optional[str] = None
    website: Optional[str] = None
    student_session_motivation: Optional[str] = None
    desired_degrees: List[str] = []
    desired_programme: List[str] = []
    desired_competences: List[str] = []
    positions: List[str] = []
    industries: List[str] = []
    employees_locally: Optional[int] = None
    employees_globally: Optional[int] = None
    jobs: List[JobSchema] = []
    has_student_session: bool = False
