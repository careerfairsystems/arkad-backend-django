from datetime import datetime, timezone, timedelta

from django.contrib.auth.models import AbstractUser
import jwt
from arkad.settings import SECRET_KEY

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
    first_name = models.CharField("first name", max_length=150, blank=True, null=True)
    last_name = models.CharField("last name", max_length=150, blank=True, null=True)

    food_preferences = models.TextField(null=True, blank=True)

    is_company = models.BooleanField(default=False)
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, default=None, null=True
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

    def create_jwt_token(self) -> str:
        return "Bearer " + jwt.encode(
            {
                "exp": datetime.now(tz=timezone.utc) + timedelta(hours=2),
                "user_id": self.id,
            },
            SECRET_KEY,
            algorithm="HS512",
        )
