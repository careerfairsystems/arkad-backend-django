from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, EmailStr


# Helper models
class UpdatedSubmittedBase(BaseModel):
    utc: Optional[datetime] = None
    clientIp: Optional[str] = None
    user: Optional[str] = None


class FileBase(BaseModel):
    size: Optional[int] = None
    name: Optional[str] = None
    type: Optional[str] = None
    file: Optional[str] = Field(None, alias="$file")
    key: Optional[str] = Field(None, alias="$$key")


# Nested schemas
class PrintContract(FileBase):
    scheduled: Optional[datetime] = None
    checksum: Optional[str] = None
    error: Optional[str] = None
    complete: Optional[datetime] = None


class Tickets(BaseModel):
    lunch_tickets_day1: Optional[int] = None
    lunch_tickets_day2: Optional[int] = None
    banquet_tickets: Optional[int] = None
    updated: Optional[UpdatedSubmittedBase] = None
    submitted: Optional[UpdatedSubmittedBase] = None


class PreregContact(BaseModel):
    inactive: Optional[bool] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class Prereg(BaseModel):
    approved: Optional[datetime | bool] = None
    contact: Optional[PreregContact] = None
    name: Optional[str] = None
    language: Optional[str] = None
    submitted: Optional[UpdatedSubmittedBase] = None


class Inventory(BaseModel):
    socket_output: Optional[str] = None
    socket_3phase: Optional[str | int] = None
    boothLarge: Optional[bool] = None
    updated: Optional[UpdatedSubmittedBase] = None
    submitted: Optional[UpdatedSubmittedBase] = None


class Billing(BaseModel):
    country: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postalCode: Optional[str] = None
    corporateId: Optional[str] = None
    corporateName: Optional[str] = None
    invoicing: Optional[str] = None
    invoiceEmail: Optional[EmailStr | str] = None
    reference: Optional[str] = None
    eInvoice: Optional[bool] = None
    corporatePO: Optional[str] = None
    requests: Optional[Any] = Field(None, alias="$requests")
    updated: Optional[UpdatedSubmittedBase] = Field(None, alias="$updated")
    submitted: Optional[UpdatedSubmittedBase] = Field(None, alias="$submitted")


class Terms(BaseModel):
    approve: Optional[bool] = None
    authorized: Optional[bool] = None
    updated: Optional[UpdatedSubmittedBase] = None
    submitted: Optional[UpdatedSubmittedBase] = None


class Inquiry(BaseModel):
    inquiryCheck: Optional[bool] = None
    desiredCompetence: List[str] = Field(default_factory=list)


class FairPkg(BaseModel):
    pkg: Optional[str] = None
    updated: Optional[UpdatedSubmittedBase] = None
    submitted: Optional[UpdatedSubmittedBase] = None


class ContactPerson(BaseModel):
    inactive: Optional[bool] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    email: Optional[EmailStr | str] = None


class ContactList(BaseModel):
    list: List[ContactPerson] = Field(default_factory=list)
    requests: Optional[Any] = Field(None, alias="$requests")
    updated: Optional[UpdatedSubmittedBase] = Field(None, alias="$updated")
    submitted: Optional[UpdatedSubmittedBase] = Field(None, alias="$submitted")


class Email(BaseModel):
    templateId: Optional[str] = None
    lastUsed: Optional[datetime] = None
    emailKey: Optional[str] = None


class TokenDevice(BaseModel):
    userAgent: Optional[str] = None
    referer: Optional[str] = None
    clientIp: Optional[str] = None
    deviceId: Optional[str] = None
    clientHints: Optional[Dict[str, Any]] = None
    utc: Optional[datetime] = None


class Token(BaseModel):
    code: Optional[str] = None
    devices: List[TokenDevice] = Field(default_factory=list)
    subject: Optional[str] = None
    utc: Optional[datetime] = None


class OrderRow(BaseModel):
    description: Optional[str] = None
    amount: Optional[int] = None
    key: Optional[str] = None
    approved: Optional[datetime] = None
    user: Optional[str] = None
    clientIp: Optional[str] = None
    included: Optional[str | int] = None  # Can be string like "2" or int like 1
    price: Optional[str] = None
    extra: Optional[int] = None


class Order(BaseModel):
    rows: List[OrderRow] = Field(default_factory=list)
    sum: Optional[int] = None
    extra: Optional[int] = None
    contractRev: Optional[datetime] = None
    approved: Optional[datetime] = None


class ExhibitionLogotype(FileBase):
    thumbs: Optional[Dict[str, Any]] = None


class Exhibition(BaseModel):
    industryCluster: Optional[str] = None
    boothSize: Optional[str] = None
    logotype: Optional[ExhibitionLogotype] = None


class Job(BaseModel):
    link: Optional[str] = None
    description: Optional[str] = None
    location: List[str] = Field(default_factory=list)
    type: List[str] = Field(default_factory=list)
    title: Optional[str] = None


class Jobs(BaseModel):
    list: List[Job] = Field(default_factory=list)


class ProfileLogotype(BaseModel):
    class Thumbs(BaseModel):
        sizes: Optional[List[int]] = None
        aspectRatio: Optional[float] = None
        complete: Optional[str] = None

    thumbs: Thumbs = Field(..., alias="$thumbs")
    size: int
    name: str
    file: str = Field(..., alias="$file")
    type: str
    key: str = Field(..., alias="$$key")


class Profile(BaseModel):
    aboutUs: Optional[str] = None
    contactEmail: Optional[EmailStr | str] = None
    contactName: Optional[str] = None
    contactTitle: Optional[str] = None
    contactPhone: Optional[str] = None
    weOffer: List[str] = Field(default_factory=list)
    industry: List[str] = Field(default_factory=list)
    didYouKnow: Optional[str] = None
    logotype: Optional[ProfileLogotype] = None
    urlWebsite: Optional[HttpUrl | str] = None
    urlFacebook: Optional[HttpUrl | str] = None
    urlLinkedin: Optional[HttpUrl | str] = None
    urlTwitter: Optional[HttpUrl | str] = None
    urlInstagram: Optional[HttpUrl | str] = None
    urlYoutube: Optional[HttpUrl | str] = None
    desiredCompetence: List[str] = Field(default_factory=list)
    desiredDegree: List[str] = Field(default_factory=list)
    desiredProgramme: List[str] = Field(default_factory=list)
    purpose: List[str] = Field(default_factory=list)
    positionsOffered: List[str] = Field(default_factory=list)
    name: Optional[str] = None
    employeesLocal: Optional[int] = None
    employeesGlobal: Optional[int] = None
    requests: Optional[dict[Any, Any]] = Field(default=None, alias="$requests")
    updated: Optional[dict[Any, Any]] = Field(default=None, alias="$updated")
    submitted: Optional[dict[Any, Any]] = Field(default=None, alias="$submitted")


class CompanyHost(BaseModel):
    key: Optional[str] = Field(None, alias="$key")
    utc: Optional[datetime] = None


class StudentSessionEvent(BaseModel):
    """Represents a student session event, e.g., studentsessions[2days]"""

    sessions: Optional[str] = None
    sessions_why: Optional[str] = None
    requests: Optional[bool] = Field(None, alias="$requests")
    updated: Optional[UpdatedSubmittedBase] = Field(None, alias="$updated")
    submitted: Optional[UpdatedSubmittedBase] = Field(None, alias="$submitted")


class Events(BaseModel):
    """
    Events object that can contain various event types including student sessions.
    Student sessions are stored with keys like 'studentsessions[2days]'
    """

    # We'll store the raw dict and provide helper methods to extract student sessions
    data: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"  # Allow any additional fields

    def get_student_session_keys(self) -> List[str]:
        """Get all keys that match the studentsessions pattern"""
        return [k for k in self.data.keys() if "studentsessions" in k.lower()]

    def get_student_session_days(self) -> Optional[int]:
        """
        Parse the number of days from studentsessions[xdays] format.
        Returns the number of days or None if not found.
        """
        for key in self.get_student_session_keys():
            # Extract number from pattern like 'studentsessions[2days]'
            import re

            match = re.search(r"\[(\d+)days?]", key)
            if match:
                return int(match.group(1))
        return None

    def get_student_session_data(self) -> Optional[Dict[str, Any]]:
        """Get the student session data if it exists"""
        keys = self.get_student_session_keys()
        if keys:
            return self.data.get(keys[0])
        return None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Events":
        """Create Events object from raw dictionary"""
        return cls(data=data)


class StudentSession(BaseModel):
    sessions: Optional[str] = None  # e.g., "none", "2days"
    requests: Optional[bool] = Field(None, alias="$requests")
    updated: Optional[UpdatedSubmittedBase] = Field(None, alias="$updated")
    submitted: Optional[UpdatedSubmittedBase] = Field(None, alias="$submitted")
    sessions_why: Optional[str] = None


# Main schema
class ExhibitorSchema(BaseModel):
    # Some are left out
    index: List[str] = Field(default_factory=list, alias="$index")
    print_contract: Optional[PrintContract] = None
    archives: List[dict[Any, Any]] = Field(default_factory=list)
    tickets: Optional[Tickets] = None
    prereg: Optional[Prereg] = None
    requests: Optional[Any] = Field(None, alias="$requests")
    inventory: Optional[Inventory] = None
    billing: Optional[Billing] = None
    current: Optional[bool] = None
    terms: Optional[Terms] = None
    inquiry: Optional[Inquiry] = None
    fairpkg: Optional[FairPkg] = None
    contact: Optional[ContactList] = None
    responsible: Optional[str] = None
    emails: List[Email] = Field(default_factory=list, alias="$emails")
    tokens: List[Token] = Field(default_factory=list, alias="$tokens")
    events: Optional[Events] = None
    order: Optional[Order] = None
    exhibition: Optional[Exhibition] = None
    period: Optional[str] = None
    updated: Optional[UpdatedSubmittedBase] = Field(None, alias="$updated")
    jobs: Optional[Jobs] = None
    profile: Optional[Profile] = None
    print_invoice: Optional[FileBase] = None
    print_order: Optional[FileBase] = None
    tags: List[str] = Field(default_factory=list)
    contract_pkg: Optional[Dict[str, Any]] = None
    exposure: Optional[Dict[str, Any]] = None
    name: Optional[str] = None
    companyHosts: List[CompanyHost] = Field(default_factory=list)
    studentsession: Optional[StudentSession] = None
    status: Optional[str] = None
    rev: Optional[datetime] = Field(None, alias="$rev")
    key: Optional[str] = Field(None, alias="$key")

    def get_student_session_days_from_events(self) -> Optional[int]:
        """
        Extract student session days from events.studentsessions[xdays].
        Returns the number of days or None if not found.
        """
        if self.events:
            return self.events.get_student_session_days()
        return None

    def get_student_session_info(self) -> Optional[Dict[str, Any]]:
        """
        Get all student session information from both studentsession field and events.
        Prioritizes events.studentsessions[xdays] over studentsession field.
        """
        # First check events for studentsessions[xdays]
        if self.events:
            event_data = self.events.get_student_session_data()
            if event_data:
                return event_data

        # Fallback to studentsession field
        if self.studentsession:
            return {
                "sessions": self.studentsession.sessions,
                "sessions_why": self.studentsession.sessions_why,
            }

        return None

    def get_combined_competences(self) -> List[str]:
        """
        Combine weOffer and desiredCompetence from profile into a unique set.
        Returns a sorted list of all unique competences.
        """
        competences = set()

        if self.profile:
            competences.update(self.profile.weOffer)
            competences.update(self.profile.desiredCompetence)

        if self.inquiry:
            competences.update(self.inquiry.desiredCompetence)

        return sorted(list(competences))

    def get_all_opportunities(self) -> List[str]:
        """
        Get all opportunities (weOffer + positionsOffered) for students.
        Returns a sorted list of unique opportunities.
        """
        opportunities = set()

        if self.profile:
            opportunities.update(self.profile.weOffer)
            opportunities.update(self.profile.positionsOffered)

        return sorted(list(opportunities))

    @classmethod
    def preprocess(cls, data: dict[Any, Any]) -> dict[Any, Any]:
        # For some reason employeesLocal and global can be strings
        employees_local = data.get("profile", {}).get("employeesLocal")
        employees_global = data.get("profile", {}).get("employeesGlobal")

        if isinstance(employees_local, str):
            if "." in employees_local:
                employees_local = employees_local.replace(".", "")
            try:
                data["profile"]["employeesLocal"] = int(employees_local)
            except ValueError:
                data["profile"]["employeesLocal"] = None
        if isinstance(employees_global, str):
            if "." in employees_global:
                employees_global = employees_global.replace(".", "")
            try:
                data["profile"]["employeesGlobal"] = int(employees_global)
            except ValueError:
                data["profile"]["employeesGlobal"] = None

        # Convert events dict to Events object if present
        if "events" in data and data["events"] and isinstance(data["events"], dict):
            data["events"] = Events.from_dict(data["events"])

        return data
