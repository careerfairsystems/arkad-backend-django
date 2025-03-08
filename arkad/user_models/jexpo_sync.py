# sync_companies.py
from typing import List, Tuple
from django.db import transaction

from user_models.company_models import Company
from user_models.jexpo_ingestion import CompanySchema
from user_models.translation import SWEDISH_TO_ENGLISH


def update_or_create_company(schema: CompanySchema) -> Tuple[Company | None, bool]:
    """
    Create or update a Company instance from a Pydantic schema.
    """
    if not schema.name or not schema.profile:
        return None, False  # Skip invalid entries

    profile = schema.profile
    logotype = profile.logotype

    # Map choices from Swedish to English
    desired_competences = [
        SWEDISH_TO_ENGLISH.get(c, c)
        for c in profile.desiredCompetence
    ]

    industries = [
        SWEDISH_TO_ENGLISH.get(i, i)
        for i in profile.industry
    ]

    # The url for the image, it uses the key for the exibitors storage. Does not append a size here.
    logo_url: str = f"https://v2cdn.jexpo.se/arkad/storage{schema.key}/{logotype.file}" if logotype else None

    # Map positions from 'weOffer' (add more mappings as needed)
    position_mapping = {
        'Heltidsjobb': 'FullTime',
        'Exjobb': 'Thesis',
        'Praktikplatser': 'Internship'
    }
    positions = [position_mapping.get(offer, offer)
                 for offer in profile.weOffer]

    # Create/update company with atomic transaction
    return Company.objects.update_or_create(
        name=schema.name,
        defaults={
            'description': profile.aboutUs,
            'did_you_know': profile.didYouKnow,
            'logo_url': logo_url,
            'website': profile.urlWebsite,
            'host_name': profile.contactName,
            'host_email': profile.contactEmail,
            'desired_degrees': profile.desiredDegree,
            'desired_programme': profile.desiredProgramme,
            'desired_competences': desired_competences,
            'positions': positions,
            'industries': industries,
        }
    )


@transaction.atomic
def sync_companies() -> List[Company]:
    """
    Fetch data from the external API and synchronize with the local database.
    Returns a list of updated or created companies.
    """
    schemas = CompanySchema.fetch()
    companies = []
    for schema in schemas:
        company = update_or_create_company(schema)
        if company:
            companies.append(company)
    return companies

if __name__ == '__main__':
    sync_companies()