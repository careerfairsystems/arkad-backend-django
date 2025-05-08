from arkad.customized_django_ninja import Schema

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


class ProfileSchema(Schema):
    id: int | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_student: bool | None = None
    cv: str | None = None
    profile_picture: str | None = None
    programme: str | None = None
    linkedin: str | None = None
    master_title: str | None = None
    study_year: int | None = None
    is_active: bool | None = None
    is_staff: bool | None = None
    food_preferences: str | None = None

class UpdateProfileSchema(Schema):
    first_name: str | None = None
    last_name: str | None = None
    programme: str | None = None
    linkedin: str | None = None
    master_title: str | None = None
    study_year: int | None = None
    food_preferences: str | None = None


class ResetPasswordSchema(Schema):
    email: str


class CompanySchema(Schema):
    id: int
    name: str
    description: str | None = None
