from enum import Enum
from arkad.customized_django_ninja import Schema


class FieldLevel(str, Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    HIDDEN = "hidden"


class FieldModificationSchema(Schema):
    """
    This allows setting some field as optional (default required) and hidden (not displayed in frontend).
    Stored as:
         {name: "field_name", field_level: FieldLevel},
    """

    name: str
    field_level: FieldLevel = FieldLevel.REQUIRED

    @classmethod
    def student_session_modifications_default(cls) -> list["FieldModificationSchema"]:
        """
        These are taken directly from StudentSessionApplicationSchema

        TODO: Make this automatically generated from the schema
        """
        return [
            cls(name="programme", field_level=FieldLevel.OPTIONAL),
            cls(name="linkedin", field_level=FieldLevel.OPTIONAL),
            cls(name="master_title", field_level=FieldLevel.OPTIONAL),
            cls(name="study_year", field_level=FieldLevel.OPTIONAL),
            cls(name="motivation_text", field_level=FieldLevel.REQUIRED),
            cls(name="cv", field_level=FieldLevel.REQUIRED),
        ]
