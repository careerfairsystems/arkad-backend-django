from ninja import Schema, ModelSchema
from user_models.models import User
from companies.models import Company


class SigninSchema(Schema):
    username: str
    password: str


class SignupSchema(Schema):
    username: str
    password: str
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None


class ProfileSchema(ModelSchema):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_student",
            "cv",
            "profile_picture",
            "programme",
            "linkedin",
            "master_title",
            "study_year",
            "is_active",
            "is_staff",
        )


class UpdateProfileSchema(ModelSchema):
    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "programme",
            "linkedin",
            "master_title",
            "study_year",
        )


class CompanySchema(ModelSchema):
    class Meta:
        model = Company
        fields = ("id", "name", "description")
