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
            first_name="Test",
            last_name="User",
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
            "foodPreferences": None,
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
            },
            content_type="application/json",
            **self.auth_headers,
        )
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


class DeleteAccountTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a regular user
        self.regular_user = User.objects.create_user(
            username="regular@example.com",
            email="regular@example.com",
            password="password123",
            first_name="Regular",
            last_name="User",
        )

        # Create a staff user
        self.staff_user = User.objects.create_user(
            username="staff@example.com",
            email="staff@example.com",
            password="password123",
            first_name="Staff",
            last_name="User",
            is_staff=True,
        )

        # Create a company user
        from companies.models import Company

        self.company = Company.objects.create(name="Test Company")
        self.company_user = User.objects.create_user(
            username="company@example.com",
            email="company@example.com",
            password="password123",
            first_name="Company",
            last_name="User",
            company=self.company,
        )

    def test_delete_account_unauthenticated(self):
        """Test that unauthenticated users cannot access the delete page"""
        response = self.client.get("/user/delete-account/")
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

        response = self.client.post("/user/delete-account/")
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

    def test_delete_account_regular_user_get(self):
        """Test that regular users can view the delete account page"""
        self.client.login(username="regular@example.com", password="password123")
        response = self.client.get("/user/delete-account/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Delete Account")
        self.assertContains(response, "This action is irreversible")

    def test_delete_account_regular_user_post(self):
        """Test that regular users can successfully delete their account"""
        self.client.login(username="regular@example.com", password="password123")
        user_id = self.regular_user.id

        # Verify user exists
        self.assertTrue(User.objects.filter(id=user_id).exists())

        # Delete account
        response = self.client.post("/user/delete-account/")

        # Should redirect after deletion
        self.assertEqual(response.status_code, 302)

        # Verify user no longer exists
        self.assertFalse(User.objects.filter(id=user_id).exists())

    def test_delete_account_staff_user_get(self):
        """Test that staff users can view the page but see a restricted message"""
        self.client.login(username="staff@example.com", password="password123")
        response = self.client.get("/user/delete-account/")

        # Should be able to access the page
        self.assertEqual(response.status_code, 200)

        # Should see the restricted message
        self.assertContains(response, "Account Deletion Restricted")
        self.assertContains(response, "contact a superadmin")

        # Should have disabled button
        self.assertContains(response, "disabled")

        # Verify staff user still exists
        self.assertTrue(User.objects.filter(id=self.staff_user.id).exists())

    def test_delete_account_staff_user_post(self):
        """Test that staff users cannot delete their account via POST"""
        self.client.login(username="staff@example.com", password="password123")
        user_id = self.staff_user.id

        response = self.client.post("/user/delete-account/")

        # Should redirect back to the delete page
        self.assertEqual(response.status_code, 302)
        self.assertIn("/user/delete-account/", response.url)

        # Verify staff user still exists
        self.assertTrue(User.objects.filter(id=user_id).exists())

    def test_delete_account_company_user_get(self):
        """Test that company users can view the page but see a restricted message"""
        self.client.login(username="company@example.com", password="password123")
        response = self.client.get("/user/delete-account/")

        # Should be able to access the page
        self.assertEqual(response.status_code, 200)

        # Should see the restricted message
        self.assertContains(response, "Account Deletion Restricted")
        self.assertContains(response, "contact a superadmin")

        # Should have disabled button
        self.assertContains(response, "disabled")

        # Verify company user still exists
        self.assertTrue(User.objects.filter(id=self.company_user.id).exists())

    def test_delete_account_company_user_post(self):
        """Test that company users cannot delete their account via POST"""
        self.client.login(username="company@example.com", password="password123")
        user_id = self.company_user.id

        response = self.client.post("/user/delete-account/")

        # Should redirect back to the delete page
        self.assertEqual(response.status_code, 302)
        self.assertIn("/user/delete-account/", response.url)

        # Verify company user still exists
        self.assertTrue(User.objects.filter(id=user_id).exists())

    def test_delete_account_with_data(self):
        """Test that deleting account also deletes associated data"""
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.client.login(username="regular@example.com", password="password123")

        # Add some data to the user
        self.regular_user.food_preferences = "Vegetarian"
        self.regular_user.programme = "Computer Engineering"
        self.regular_user.cv = SimpleUploadedFile(
            "cv.pdf", b"file_content", content_type="application/pdf"
        )
        self.regular_user.profile_picture = SimpleUploadedFile(
            "profile.jpg", b"file_content", content_type="image/jpeg"
        )
        self.regular_user.save()

        user_id = self.regular_user.id

        # Delete account
        self.client.post("/user/delete-account/")

        # Verify user and all data no longer exists
        self.assertFalse(User.objects.filter(id=user_id).exists())

    def test_delete_account_removes_files_from_filesystem(self):
        """Test that deleting account also removes files from the filesystem"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        import os

        self.client.login(username="regular@example.com", password="password123")

        # Add files to the user
        cv_file = SimpleUploadedFile(
            "test_cv.pdf", b"cv_file_content", content_type="application/pdf"
        )
        profile_pic_file = SimpleUploadedFile(
            "test_profile.jpg", b"profile_pic_content", content_type="image/jpeg"
        )

        self.regular_user.cv = cv_file
        self.regular_user.profile_picture = profile_pic_file
        self.regular_user.save()

        # Get the file paths
        cv_path = self.regular_user.cv.path
        profile_pic_path = self.regular_user.profile_picture.path

        # Verify files exist on filesystem
        self.assertTrue(os.path.exists(cv_path), "CV file should exist before deletion")
        self.assertTrue(
            os.path.exists(profile_pic_path),
            "Profile picture should exist before deletion",
        )

        # Delete account
        self.client.post("/user/delete-account/")

        # Verify user no longer exists
        self.assertFalse(User.objects.filter(id=self.regular_user.id).exists())

        # Verify files are removed from filesystem
        self.assertFalse(
            os.path.exists(cv_path), "CV file should be deleted from filesystem"
        )
        self.assertFalse(
            os.path.exists(profile_pic_path),
            "Profile picture should be deleted from filesystem",
        )
