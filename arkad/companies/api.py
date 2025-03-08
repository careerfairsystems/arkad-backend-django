from django.http import HttpRequest
from ninja import Router

from companies.models import Company
from companies.schema import CompanyOut

router = Router(tags=["Companies"])

@router.get("/", response={200: list[CompanyOut]})
def get_companies(request: HttpRequest):
    return Company.objects.all()
