from arkad.auth import OPTIONAL_AUTH
from arkad.customized_django_ninja import Router, ListType
from user_models.models import AuthenticatedRequest
from companies.models import Company
from companies.schema import CompanyOut

router = Router(tags=["Companies"])


@router.get("/", response={200: ListType[CompanyOut]}, auth=OPTIONAL_AUTH)
def get_companies(request: AuthenticatedRequest):
    """
    Returns all mostly public information about companies (days with student sessions are also included).
    """
    return Company.objects.prefetch_related("jobs").all()


# We should probably not be able to change company information by api here, instead require Jexpo update.
# Otherwise, we risk overwriting it.
