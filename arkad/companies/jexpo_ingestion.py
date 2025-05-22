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


class ContactList(BaseModel):
    inactive: Optional[bool] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None


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
    name: Optional[str] = None
    employeesLocal: Optional[str] = None
    employeesGlobal: Optional[str] = None
    requests: Optional[dict[Any, Any]] = Field(default=None, alias="$requests")
    updated: Optional[dict[Any, Any]] = Field(default=None, alias="$updated")
    submitted: Optional[dict[Any, Any]] = Field(default=None, alias="$submitted")


class CompanyHost(BaseModel):
    key: Optional[str] = Field(None, alias="$key")
    utc: Optional[datetime] = None


class StudentSession(BaseModel):
    sessions: Optional[str] = None  # e.g., "none"
    requests: Optional[bool] = Field(None, alias="$requests")
    updated: Optional[UpdatedSubmittedBase] = Field(None, alias="$updated")
    submitted: Optional[UpdatedSubmittedBase] = Field(None, alias="$submitted")
    sessions_why: Optional[str] = None


# Main schema
class ExhibitorSchema(BaseModel):
    # Some are left out
    index: List[str] = Field(default_factory=list, alias="$index")
    print_contract: Optional[PrintContract] = None
    archives: List[str] = Field(default_factory=list)
    tickets: Optional[Tickets] = None
    prereg: Optional[Prereg] = None
    requests: Optional[bool] = Field(None, alias="$requests")
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
    events: Optional[Dict[str, Any]] = None
    order: Optional[Dict[str, Any]] = None
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
