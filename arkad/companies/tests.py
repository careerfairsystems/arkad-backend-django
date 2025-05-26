from django.test import TestCase, Client

from companies.models import Company
from user_models.models import User


class FavouriteTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.student_users = []
        for i in range(5):
            self.student_users.append(
                User.objects.create_user(
                    first_name="Student" + str(i),
                    last_name="Student" + str(i),
                    email="a@student.com",
                    password="PASSWORD",
                    username="Student" + str(i),
                    is_student=True,
                    is_company=False,
                )
            )
        self.client = Client()

    @staticmethod
    def _get_auth_headers(user: User) -> dict:
        return {"Authorization": user.create_jwt_token()}
    
    def test_get_favourites_noauth(self):
        resp = self.client.get(
            "/api/company/",
        )
        self.assertEqual(resp.status_code, 200)
        response_data = resp.json()
        self.assertGreater(len(response_data), 0)
        company = response_data[0]
        self.assertIsNone(company["is_favourite"])
    


