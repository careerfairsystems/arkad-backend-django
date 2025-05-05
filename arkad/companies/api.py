from arkad import Router
from user_models.models import AuthenticatedRequest
from companies.models import Company
from companies.schema import CompanyOut

router = Router(tags=["Companies"])


@router.get("/", response={200: list[CompanyOut]}, auth=None)
def get_companies(request: AuthenticatedRequest):
    """
    Returns all mostly public information about companies (days with student sessions are also included).
    """
    return Company.objects.all()

# We should probably not be able to change company information by api here, instead require Jexpo update.
# Otherwise, we risk overwriting it.
