from datetime import datetime, timezone, timedelta
from django.contrib.auth.models import AbstractUser
from arkad.jwt_utils import jwt_encode
from django.db import models
from companies.models import Company


class Programme(models.TextChoices):
    BRANDINGENJOR = "Brandingenjör"
    MASKINTEKNIK_TD = "Maskinteknik_Teknisk_Design"
    ELEKTROTEKNIK = "Elektroteknik"
    EKOSYSTEMTEKNIK = "Ekosystemteknik"
    MASKINTEKNIK = "Maskinteknik"
    NANOVETEKNIK = "Nanoveteknik"
    BIOTEKNIK = "Bioteknik"
    INDUSTRIDESIGN = "Industridesign"
    ARKITEKT = "Arkitekt"
    INFOKOMM_TEKNIK = "Informations och Kommunikationsteknik"
    KEMITEKNIK = "Kemiteknik"
    BYGG_JARNVAG = "Byggteknik med Järnvägsteknik"
    VAG_VATTEN = "Väg och vatttenbyggnad"
    BYGG_ARKITEKTUR = "Byggteknik med arkitektur"
    INDUSTRIELL_EKONOMI = "Industriell ekonomi"
    TEKNISK_MATEMATIK = "Teknisk Matematik"
    MEDICINTEKNIK = "Medicinteknik"
    LANTMATERI = "Lantmäteri"
    DATATEKNIK = "Datateknik"
    TEKNISK_FYSIK = "Teknisk Fysik"
    BYGG_VAG_TRAFIK = "Byggteknik med väg och trafikteknik"


class User(AbstractUser):
    first_name = models.CharField("first name", max_length=150, blank=True, null=True)  # type: ignore[misc]
    last_name = models.CharField("last name", max_length=150, blank=True, null=True)  # type: ignore[misc]

    food_preferences = models.TextField(null=True, blank=True)

    is_company = models.BooleanField(default=False)
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, default=None, null=True, blank=True
    )

    is_student = models.BooleanField(default=True)
    cv = models.FileField("Users cv", upload_to="user/cv", null=True, blank=True)
    profile_picture = models.FileField(
        "User profile picture", upload_to="user/profile-pictures", blank=True, null=True
    )

    programme = models.CharField(
        max_length=64, choices=Programme.choices, blank=True, null=True
    )
    linkedin = models.URLField(blank=True, null=True)
    master_title = models.CharField(max_length=255, blank=True, null=True)
    study_year = models.IntegerField(blank=True, null=True)

    def __str__(self) -> str:
        name: str = (self.first_name or "") + " " + (self.last_name or "")
        if self.first_name is None and self.last_name is None:
            return self.email
        return name

    def create_jwt_token(self, expiry_hours: int = 96) -> str:
        return "Bearer " + jwt_encode(
            {
                "exp": datetime.now(tz=timezone.utc) + timedelta(hours=expiry_hours),
                "user_id": self.id,
            },
        )

    def is_company_admin(self, company_id: int) -> bool:
        return self.is_company and self.company_id == company_id
