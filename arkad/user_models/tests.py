from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()

class UserAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="strongpassword",
            first_name="Test",
            last_name="User",
        )

    def test_signup_success(self):
        payload = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpassword",
            "first_name": "New",
            "last_name": "User",
        }
        response = self.client.post("/api/user/signup", data=payload, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "newuser")

    def test_signup_duplicate_username(self):
        payload = {
            "username": "testuser",  # Already exists
            "email": "duplicate@example.com",
            "password": "duplicatepassword",
            "first_name": "Duplicate",
            "last_name": "User",
        }
        response = self.client.post("/api/user/signup", data=payload, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), "Username already exists")

    def test_signin_success(self):
        signin_payload = {"username": "testuser", "password": "strongpassword"}
        response = self.client.post("/api/user/signin", data=signin_payload, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Bearer ", response.json())

    def test_signin_invalid_credentials(self):
        signin_payload = {"username": "testuser", "password": "wrongpassword"}
        response = self.client.post("/api/user/signin", data=signin_payload, content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), "Invalid username or password")

    def test_profile_authenticated(self):

        signin_payload = {"username": "testuser", "password": "strongpassword"}
        response = self.client.post("/api/user/signin", data=signin_payload, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        response = self.client.get("/api/user/profile",
                                   headers={"Authorization": response.content.decode("utf-8").strip('"')})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "testuser")

    def test_profile_unauthenticated(self):
        response = self.client.get("/api/user/profile")
        self.assertEqual(response.status_code, 401)
