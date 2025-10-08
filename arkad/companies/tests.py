# Create your tests here.
from django.test import TestCase
from .models import Company


class TestGetCompanies(TestCase):
    def setUp(self):
        # Create companies
        Company.objects.create(name="Company A", description="Description A")
        Company.objects.create(name="Company B", description="Description B")
        Company.objects.create(name="Company C", description="Description C")

    def test_get_companies_api(self):
        response = self.client.get("/api/company/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 3)
        company_names = {company["name"] for company in data}
        self.assertSetEqual(company_names, {"Company A", "Company B", "Company C"})
