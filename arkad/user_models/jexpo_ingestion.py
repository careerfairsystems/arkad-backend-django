import requests
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class SubmittedUpdatedSchema(BaseModel):
    utc: Optional[datetime] = None

class JobsSchema(BaseModel):
    submitted: Optional[SubmittedUpdatedSchema] = Field(alias="$submitted", default=None)
    updated: Optional[SubmittedUpdatedSchema] = Field(alias="$updated", default=None)

class ThumbsSchema(BaseModel):
    aspect_ratio: Optional[float] = Field(alias="aspectRatio", default=None)
    complete: Optional[datetime] = None
    sizes: List[int] = Field(default_factory=list)

class LogotypeSchema(BaseModel):
    file: Optional[str] = Field(alias="$file", default=None)
    thumbs: Optional[ThumbsSchema] = Field(alias="$thumbs", default=None)
    name: Optional[str] = None
    size: Optional[int] = None
    type: Optional[str] = None

class ProfileSchema(BaseModel):
    submitted: Optional[SubmittedUpdatedSchema] = Field(alias="$submitted", default=None)
    updated: Optional[SubmittedUpdatedSchema] = Field(alias="$updated", default=None)
    aboutUs: Optional[str] = None
    contactEmail: Optional[str] = None
    contactName: Optional[str] = None
    contactTitle: Optional[str] = None
    desiredCompetence: List[str] = Field(default_factory=list)
    desiredDegree: List[str] = Field(default_factory=list)
    desiredProgramme: List[str] = Field(default_factory=list)
    didYouKnow: Optional[str] = None
    employeesGlobal: Optional[str] = None
    employeesLocal: Optional[str] = None
    industry: List[str] = Field(default_factory=list)
    logotype: Optional[LogotypeSchema] = None
    name: Optional[str] = None
    purpose: List[str] = Field(default_factory=list)
    urlLinkedin: Optional[str] = None
    urlWebsite: Optional[str] = None
    weOffer: List[str] = Field(default_factory=list)

class CompanySchema(BaseModel):
    index: List[str] = Field(default_factory=list, alias="$index")
    key: Optional[str] = Field(alias="$key", default=None)
    rev: Optional[datetime] = Field(alias="$rev", default=None)
    jobs: Optional[JobsSchema] = None
    name: Optional[str] = None
    profile: Optional[ProfileSchema] = None

    @classmethod
    def fetch(cls) -> list["CompanySchema"]:
        url: str = "https://v2cdn.jexpo.se/arkad/entities/exhibitors?filter=period:2024&entities"
        return [cls(**result) for result in requests.get(url).json()["results"]]
