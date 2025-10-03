from typing import cast, Any

from import_export import resources, fields, widgets
from .models import StudentSessionApplication


class StudentSessionApplicationStatusWidget(widgets.CharWidget):
    """
    Custom widget to handle status values during import/export. Makes sure that the status value is one of the valid choices.
    """

    def clean(self, value: Any, row: Any = None, *args: Any, **kwargs: Any) -> Any:
        valid_statuses = StudentSessionApplication.get_valid_statuses()
        if value not in valid_statuses:
            raise ValueError(
                f"Invalid status '{value}'. Valid statuses are: {valid_statuses}"
            )
        return super().clean(value, row, *args, **kwargs)


class StudentSessionApplicationResource(resources.ModelResource):  # type: ignore[type-arg]
    """
    Resource for importing and exporting StudentSessionApplication data.

    Export includes related user and company information.
    Import is designed to only update the 'status' of an existing application.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        self.request = kwargs.pop("request", None)
        super(StudentSessionApplicationResource, self).__init__(*args, **kwargs)

    # The only mutable field "status"
    status = fields.Field(
        attribute="status",
        column_name="Status",
        widget=StudentSessionApplicationStatusWidget(),
    )

    # Fields from the Application model
    motivation_text = fields.Field(
        attribute="motivation_text", column_name="Motivation", readonly=True
    )
    timestamp = fields.Field(
        attribute="timestamp", column_name="Application Time", readonly=True
    )

    # Fields from the related User model
    first_name = fields.Field(
        attribute="user__first_name", column_name="First Name", readonly=True
    )
    last_name = fields.Field(
        attribute="user__last_name", column_name="Last Name", readonly=True
    )
    email = fields.Field(attribute="user__email", column_name="Email", readonly=True)
    programme = fields.Field(
        attribute="user__programme", column_name="Programme", readonly=True
    )
    study_year = fields.Field(
        attribute="user__study_year", column_name="Study Year", readonly=True
    )
    master_title = fields.Field(
        attribute="user__master_title", column_name="Master Title", readonly=True
    )
    linkedin = fields.Field(
        attribute="user__linkedin", column_name="LinkedIn", readonly=True
    )

    # Field from the related Company model
    company = fields.Field(
        attribute="student_session__company__name", column_name="Company", readonly=True
    )

    # Custom field for the CV
    cv = fields.Field(column_name="CV", readonly=True)

    def dehydrate_cv(self, application: StudentSessionApplication) -> str:
        """
        Gets the absolute URL for the CV.
        """
        cv_file = application.cv or application.user.cv
        if cv_file and hasattr(cv_file, "url"):
            # If we have a request object, build an absolute URI.
            if self.request:
                return str(self.request.build_absolute_uri(cv_file.url))
            # Fallback to the relative URL if no request is available.
            return str(cv_file.url)
        return ""

    class Meta:
        model = StudentSessionApplication

        # This is the key for matching records during import.
        # We use the application's unique ID.
        import_id_fields = ("id",)

        # Define the fields to be included in the export/import file.
        # 'id' is crucial for matching records on import.
        # 'status' is the only field companies should change.
        fields = (
            "id",
            "company",
            "status",
            "first_name",
            "last_name",
            "email",
            "motivation_text",
            "programme",
            "study_year",
            "master_title",
            "linkedin",
            "cv",
            "timestamp",
        )

        # This ensures that during import, if a row in the file hasn't changed,
        # it won't be processed.
        skip_unchanged = True

        # Report which rows were skipped.
        report_skipped = True
