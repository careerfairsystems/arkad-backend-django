# sync_companies.py
from typing import Tuple

from companies.models import Company, Job
from companies.jexpo_ingestion import ExhibitorSchema
from companies.translation import SWEDISH_TO_ENGLISH


def update_or_create_company(schema: ExhibitorSchema) -> Tuple[Company | None, bool]:
    """
    Create or update a Company instance from a Pydantic schema.
    """
    if not schema.name or not schema.profile:
        return None, False  # Skip invalid entries

    profile = schema.profile
    logotype = profile.logotype

    # Map choices from Swedish to English
    desired_competences = [
        SWEDISH_TO_ENGLISH.get(c, c) for c in profile.desiredCompetence
    ]

    industries = [SWEDISH_TO_ENGLISH.get(i, i) for i in profile.industry]

    # The url for the image, it uses the key for the exibitors storage. Does not append a size here.
    logo_url: str = (
        f"https://v2cdn.jexpo.se/arkad/storage{schema.key}/{logotype.file}"
        if logotype
        else None
    )

    # Map positions from 'weOffer' (add more mappings as needed)
    position_mapping = {
        "Heltidsjobb": "FullTime",
        "Exjobb": "Thesis",
        "Praktikplatser": "Internship",
    }
    positions = [position_mapping.get(offer, offer) for offer in profile.weOffer]
    # schema.studentsession.sessions is either None or xdays where x is an integer
    # Will read as many numerical prepended numbers as possible.
    # xxxx works
    # axxx will give 0

    parse_session_days: int = 0
    sessions: str | None = (
        schema.studentsession.sessions if schema.studentsession else None
    )
    if sessions is not None:
        # This is not the prettiest way to do this but easy to read
        numerical_chars: list[int] = []
        for i, char in enumerate(sessions):
            if char.isnumeric():
                numerical_chars.append(int(char))
            else:
                break
        parse_session_days = sum(
            ((10**i) * d for i, d in enumerate(reversed(numerical_chars), start=0))
        )
    # Create/update company with atomic transaction
    company, created = Company.objects.update_or_create(
        name=schema.name,
        defaults={
            "description": profile.aboutUs,
            "did_you_know": profile.didYouKnow,
            "logo_url": logo_url,
            "url_linkedin": profile.urlLinkedin,
            "url_facebook": profile.urlFacebook,
            "url_twitter": profile.urlTwitter,
            "url_instagram": profile.urlInstagram,
            "url_youtube": profile.urlYoutube,
            "website": profile.urlWebsite,
            "company_name": profile.contactName,
            "company_email": profile.contactEmail,
            "company_phone": profile.contactPhone,
            "desired_degrees": profile.desiredDegree,
            "desired_programme": profile.desiredProgramme,
            "desired_competences": desired_competences,
            "positions": positions,
            "industries": industries,
            "student_session_motivation": schema.studentsession.sessions_why
            if schema.studentsession
            else None,
            "days_with_studentsession": parse_session_days,
            "employees_locally": int(profile.employeesLocal.replace(".", ""))
            if profile.employeesLocal
            else None,
            "employees_globally": int(profile.employeesGlobal.replace(".", ""))
            if profile.employeesGlobal
            else None,
        },
    )
    if schema.jobs is not None:
        jobs: list[Job] = [
            Job.objects.create(
                link=job.link,
                description=job.description,
                location=job.location,
                title=job.title,
                job_type=job.type,
            )
            for job in schema.jobs.list
        ]

        # Remove old jobs
        for j in company.jobs.all():
            j.delete()
        company.jobs.set(jobs)
        company.save()
    return company, created
