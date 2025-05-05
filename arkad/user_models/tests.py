from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from arkad.jwt_utils import jwt_encode, jwt_decode, PUBLIC_KEY

User = get_user_model()


class UserSignin(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="strongpassword",
            first_name="Test",
            last_name="User",
        )

    def test_signin_success(self):
        signin_payload = {"email": "test@example.com", "password": "strongpassword"}
        response = self.client.post(
            "/api/user/signin", data=signin_payload, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Bearer ", response.json())

    def test_signin_invalid_credentials(self):
        signin_payload = {"email": "test@example.com", "password": "wrongpassword"}
        response = self.client.post(
            "/api/user/signin", data=signin_payload, content_type="application/json"
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), "Invalid email or password")

    def test_profile_authenticated(self):
        signin_payload = {"email": "test@example.com", "password": "strongpassword"}
        response = self.client.post(
            "/api/user/signin", data=signin_payload, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            "/api/user/profile",
            headers={"Authorization": response.json()},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "test@example.com")

    def test_profile_unauthenticated(self):
        response = self.client.get("/api/user/profile")
        self.assertEqual(response.status_code, 401)


class UserRoutesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser@example.com",
            password="password123",
            email="testuser@example.com",
        )
        self.token = self.client.post(
            "/api/user/signin",
            {"email": "testuser@example.com", "password": "password123"},
            content_type="application/json",
        ).json()
        self.assertIn("Bearer", self.token)
        self.auth_headers = {"headers": {"Authorization": self.token}}

    def test_signin(self):
        data = {"email": "testuser@example.com", "password": "password123"}
        response = self.client.post(
            "/api/user/signin", data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), str)  # JWT token expected

        data_invalid = {"email": "testuser@example.com", "password": "wrongpassword"}
        response_invalid = self.client.post(
            "/api/user/signin", data_invalid, content_type="application/json"
        )
        self.assertEqual(response_invalid.status_code, 401)
        self.assertEqual(response_invalid.json(), "Invalid email or password")

    def test_get_user_profile(self):
        response = self.client.get("/api/user/profile", **self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "testuser@example.com")

    def test_update_profile(self):
        upd_data_camel_case = {
            "firstName": "New",
            "lastName": "Name",
            "programme": "CS",
            "linkedin": "linkedin.com/in/test",
            "masterTitle": "Master",
            "studyYear": 2,
            "foodPreferences": None
        }
        response = self.client.put(
            "/api/user/profile",
            upd_data_camel_case,
            content_type="application/json",
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, 200, response.json())
        data = response.json()
        u = User.objects.get(pk=data["id"])
        # Check so that user was updated correctly
        self.assertEqual(data["firstName"], u.first_name)
        self.assertEqual(data["lastName"], u.last_name)
        self.assertEqual(data["programme"], u.programme)
        self.assertEqual(data["linkedin"], u.linkedin)
        self.assertEqual(data["masterTitle"], u.master_title)
        self.assertEqual(data["studyYear"], u.study_year)
        self.assertEqual(data["foodPreferences"], u.food_preferences)

        # Now test same as above but with snake case instead. Should do the same thing,
        # Test by changing the first and lastname

        response = self.client.put(
            "/api/user/profile",
            {
                "first_name": "snake",
                "last_name": "case",
            }, content_type="application/json",
            **self.auth_headers)
        self.assertEqual(response.status_code, 200, response.json())
        data = response.json()
        u = User.objects.get(pk=data["id"])
        # Check so that user was updated correctly
        self.assertEqual(data["firstName"], u.first_name)
        self.assertEqual(data["lastName"], u.last_name)


    def test_update_profile_fields(self):
        data = {
            "first_name": "Updated",
            "last_name": "User",
        }
        response = self.client.patch(
            "/api/user/profile",
            data,
            content_type="application/json",
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, 200, response.json())
        u = User.objects.get(pk=response.json()["id"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["firstName"], "Updated")
        self.assertEqual(response.json()["lastName"], "User")
        self.assertEqual(u.first_name, "Updated")
        self.assertEqual(u.last_name, "User")

    def test_update_profile_picture(self):
        file = SimpleUploadedFile(
            "profile.jpg", b"file_content", content_type="image/jpeg"
        )
        response = self.client.post(
            "/api/user/profile/profile-picture",
            {"profile_picture": file},
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "Profile picture updated")

    def test_update_cv(self):
        file = SimpleUploadedFile(
            "cv.pdf", b"file_content", content_type="application/pdf"
        )
        response = self.client.post(
            "/api/user/profile/cv", {"cv": file}, **self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "CV updated")

    def test_delete_profile_picture_existing(self):
        file = SimpleUploadedFile(
            "profile.jpg", b"file_content", content_type="image/jpeg"
        )
        self.assertEqual(
            200,
            self.client.post(
                "/api/user/profile/profile-picture",
                {"profile_picture": file},
                **self.auth_headers,
            ).status_code,
        )
        response = self.client.delete(
            "/api/user/profile/profile-picture", **self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "Profile picture deleted")

    def test_delete_profile_picture_nonexistent(self):
        response = self.client.delete(
            "/api/user/profile/profile-picture", **self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "Profile picture deleted")

    def test_delete_cv_existing(self):
        file = SimpleUploadedFile(
            "cv.pdf", b"file_content", content_type="application/pdf"
        )
        self.assertEqual(
            200,
            self.client.post(
                "/api/user/profile/cv",
                {"cv": file},
                headers={"Authorization": self.token},
            ).status_code,
        )
        response = self.client.delete("/api/user/profile/cv", **self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "CV deleted")

    def test_delete_cv_nonexistent(self):
        response = self.client.delete("/api/user/profile/cv", **self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "CV deleted")


class AuthenticationTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_asymmetric_jwt(self):
        message: str = "Hello World!"
        self.assertEqual(jwt_decode(jwt_encode({"msg": message}))["msg"], message)

    def test_asymmetric_jwt_public_key_endpoint(self):
        resp = self.client.get("/api/get-public-key")
        self.assertEqual(200, resp.status_code)
        self.maxDiff = None
        self.assertEqual(PUBLIC_KEY, resp.json()["publicKey"])
