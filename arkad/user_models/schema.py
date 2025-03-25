from ninja import Schema, ModelSchema
from user_models.models import User
from companies.models import Company


class SigninSchema(Schema):
    email: str
    password: str


class SignupSchema(Schema):
    password: str
    first_name: str | None = None
    last_name: str | None = None
    email: str

class CompleteSignupSchema(Schema):
    token: str
    code: str
    password: str
    first_name: str | None = None
    last_name: str | None = None
    email: str

class ProfileSchema(ModelSchema):
    class Meta:
        model = User
        fields = (
            "id",
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
