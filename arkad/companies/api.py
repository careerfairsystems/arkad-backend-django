from arkad.customized_django_ninja import Router
from user_models.models import AuthenticatedRequest, Favourites
from companies.models import Company
from companies.schema import CompanyOut

router = Router(tags=["Companies"])

@router.get("/", response={200: list[CompanyOut]}, auth=None)
def get_companies(request: AuthenticatedRequest):
    """
    Returns all mostly public information about companies (days with student sessions are also included).
    """

    favourite_company_ids = set()
    if request.user.is_authenticated:
        favourite_company_ids = set(
            Favourites.objects.filter(user=request.user)
            .values_list('company_id', flat=True)
        )

    companies_orm = Company.objects.all()
    companies_output = []
    for company in companies_orm:
        companyOut_instance = CompanyOut.from_orm(company)
        if not request.user.is_authenticated:
            companyOut_instance.is_favourite = None
        else:
            if company.id in favourite_company_ids:
                companyOut_instance.is_favourite = True
            else:
                companyOut_instance.is_favourite = False
            companies_output.append(companyOut_instance)
    return companies_output

# We should probably not be able to change company information by api here, instead require Jexpo update.
# Otherwise, we risk overwriting it.
