from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSignin(TestCase):
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


class UserRoutesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.token = self.client.post("/api/user/signin", {"username": "testuser", "password": "password123"}, content_type="application/json").json()
        self.auth_headers = {"HTTP_AUTHORIZATION": self.token}

    def test_signup(self):
        data = {"username": "newuser", "password": "securepassword"}
        response = self.client.post("/api/user/signup", data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "newuser")

        response_duplicate = self.client.post("/api/user/signup", data, content_type="application/json")
        self.assertEqual(response_duplicate.status_code, 400)
        self.assertEqual(response_duplicate.json(), "Username already exists")

    def test_signin(self):
        data = {"username": "testuser", "password": "password123"}
        response = self.client.post("/api/user/signin", data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), str)  # JWT token expected

        data_invalid = {"username": "testuser", "password": "wrongpassword"}
        response_invalid = self.client.post("/api/user/signin", data_invalid, content_type="application/json")
        self.assertEqual(response_invalid.status_code, 401)
        self.assertEqual(response_invalid.json(), "Invalid username or password")

    def test_get_user_profile(self):
        response = self.client.get("/api/user/profile", **self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "testuser")

    def test_update_profile(self):
        upd_data = {
            "email": "newemail@example.com",
            "first_name": "New",
            "last_name": "Name",
            "programme": "CS",
            "linkedin": "linkedin.com/in/test",
            "master_title": "Master",
            "study_year": 2
        }
        response = self.client.put("/api/user/profile", upd_data, content_type="application/json", **self.auth_headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        u = User.objects.get(pk=data["id"])
        for k, v in upd_data.items():
            self.assertEqual(data[k], v)
            self.assertEqual(v, u.__dict__[k])


    def test_update_profile_picture(self):
        file = SimpleUploadedFile("profile.jpg", b"file_content", content_type="image/jpeg")
        response = self.client.post("/api/user/profile/profile-picture", {"profile_picture": file}, **self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "Profile picture updated")

    def test_update_cv(self):
        file = SimpleUploadedFile("cv.pdf", b"file_content", content_type="application/pdf")
        response = self.client.post("/api/user/profile/cv", {"cv": file}, **self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "CV updated")
