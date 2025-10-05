from functools import partial
from typing import Any

from django.contrib.auth.models import AbstractUser
from pydantic import BaseModel, GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

from arkad.jwt_utils import jwt_encode
from django.db import models

from arkad.utils import unique_file_upload_path
from companies.models import Company


class Programme(models.TextChoices):
    BRANDINGENJOR = "Fire Engineering"
    MASKINTEKNIK_TD = "Mechanical Engineering with Technical Design"
    ELEKTROTEKNIK = "Electrical Engineering"
    EKOSYSTEMTEKNIK = "Environmental Engineering"
    MASKINTEKNIK = "Mechanical Engineering"
    NANOVETEKNIK = "Nanoscience and Technology"
    BIOTEKNIK = "Biotechnology"
    INDUSTRIDESIGN = "Industrial Design"
    ARKITEKT = "Architecture"
    INFOKOMM_TEKNIK = "Information and Communication Engineering"
    KEMITEKNIK = "Chemical Engineering"
    BYGG_JARNVAG = "Civil Engineering with Railway Engineering"
    VAG_VATTEN = "Road and Water Engineering"
    BYGG_ARKITEKTUR = "Civil Engineering with Architecture"
    INDUSTRIELL_EKONOMI = "Industrial Engineering and Management"
    TEKNISK_MATEMATIK = "Engineering Mathematics"
    MEDICINTEKNIK = "Biomedical Engineering"
    LANTMATERI = "Surveying"
    DATATEKNIK = "Computer Engineering"
    TEKNISK_FYSIK = "Engineering Physics"
    BYGG_VAG_TRAFIK = "Civil Engineering with Road and Traffic Engineering"


# Translation mappings for Programme names
PROGRAMME_ENGLISH_TO_SWEDISH: dict[str, str] = {
    "Fire Engineering": "Brandingenjör",
    "Mechanical Engineering with Technical Design": "Maskinteknik_Teknisk_Design",
    "Electrical Engineering": "Elektroteknik",
    "Environmental Engineering": "Ekosystemteknik",
    "Mechanical Engineering": "Maskinteknik",
    "Nanoscience and Technology": "Nanoveteknik",
    "Biotechnology": "Bioteknik",
    "Industrial Design": "Industridesign",
    "Architecture": "Arkitekt",
    "Information and Communication Engineering": "Informations och Kommunikationsteknik",
    "Chemical Engineering": "Kemiteknik",
    "Civil Engineering with Railway Engineering": "Byggteknik med Järnvägsteknik",
    "Road and Water Engineering": "Väg och vatttenbyggnad",
    "Civil Engineering with Architecture": "Byggteknik med arkitektur",
    "Industrial Engineering and Management": "Industriell ekonomi",
    "Engineering Mathematics": "Teknisk Matematik",
    "Biomedical Engineering": "Medicinteknik",
    "Surveying": "Lantmäteri",
    "Computer Engineering": "Datateknik",
    "Engineering Physics": "Teknisk Fysik",
    "Civil Engineering with Road and Traffic Engineering": "Byggteknik med väg och trafikteknik",
}

PROGRAMME_SWEDISH_TO_ENGLISH: dict[str, str] = {
    v: k for k, v in PROGRAMME_ENGLISH_TO_SWEDISH.items()
}


def translate_programme_to_swedish(english_name: str) -> str:
    """Translate a programme name from English to Swedish.

    Args:
        english_name: The English programme name

    Returns:
        The Swedish translation, or the original name if not found
    """
    return PROGRAMME_ENGLISH_TO_SWEDISH.get(english_name, english_name)


def translate_programme_to_english(swedish_name: str) -> str:
    """Translate a programme name from Swedish to English.

    Args:
        swedish_name: The Swedish programme name

    Returns:
        The English translation, or the original name if not found
    """
    return PROGRAMME_SWEDISH_TO_ENGLISH.get(swedish_name, swedish_name)


class User(AbstractUser):
    first_name = models.CharField("first name", max_length=150, blank=True, null=True)  # type: ignore[misc]
    last_name = models.CharField("last name", max_length=150, blank=True, null=True)  # type: ignore[misc]

    food_preferences = models.TextField(null=True, blank=True)

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, default=None, null=True, blank=True
    )

    is_student = models.BooleanField(default=True)
    cv = models.FileField(
        "Users cv",
        upload_to=partial(unique_file_upload_path, "user/cv"),
        null=True,
        blank=True,
    )
    profile_picture = models.FileField(
        "User profile picture",
        upload_to=partial(unique_file_upload_path, "user/profile-picture"),
        blank=True,
        null=True,
    )

    programme = models.CharField(
        max_length=64, choices=Programme.choices, blank=True, null=True
    )
    linkedin = models.URLField(blank=True, null=True)
    master_title = models.CharField(max_length=255, blank=True, null=True)
    study_year = models.IntegerField(blank=True, null=True)

    fcm_token = models.TextField(null=True, blank=True)

    @property
    def is_company(self) -> bool:
        return self.company is not None

    def __str__(self) -> str:
        name: str = (self.first_name or "") + " " + (self.last_name or "")
        if self.first_name is None and self.last_name is None:
            return self.email
        return name

    def create_jwt_token(self, expiry_days: int = 30) -> str:
        return "Bearer " + jwt_encode(
            {
                "user_id": self.id,
            },
            expiry_minutes=expiry_days * 24 * 60,
        )

    def get_auth_headers(self) -> dict[str, str]:
        return {"Authorization": self.create_jwt_token()}


class PydanticUser:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            handler(User),  # Or use handler.generate_schema(User) if recursion occurs
        )

    @classmethod
    def validate(cls, v: Any) -> User:
        if not isinstance(v, User):
            raise ValueError("Expected User instance")
        return v


class AuthenticatedRequest(BaseModel):
    user: "User"  # Forward reference if needed

    class Config:
        arbitrary_types_allowed = True
