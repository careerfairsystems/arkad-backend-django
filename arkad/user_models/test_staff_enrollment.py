"""
Tests for Staff Enrollment API endpoints
"""

from django.test import TestCase, Client
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
from unittest.mock import patch
from typing import Any
import json

from user_models.models import User, StaffEnrollmentToken, StaffEnrollmentUsage
from arkad.jwt_utils import jwt_encode
from hashlib import sha256
from arkad.settings import SECRET_KEY


class StaffEnrollmentAPITestCase(TestCase):
    """Test cases for staff enrollment API endpoints"""

    def setUp(self) -> None:
        """Set up test data"""
        self.client = Client()
        cache.clear()

        # Create a superuser to create enrollment tokens
        self.superuser = User.objects.create_superuser(
            username="admin@example.com",
            email="admin@example.com",
            password="AdminPass123!",
            first_name="Admin",
            last_name="User",
        )

        # Create a valid enrollment token
        self.valid_token = StaffEnrollmentToken.objects.create(
            token="valid_test_token_123",
            created_by=self.superuser,
            expires_at=timezone.now() + timedelta(days=7),
            is_active=True,
        )

        # Create an expired token
        self.expired_token = StaffEnrollmentToken.objects.create(
            token="expired_test_token_456",
            created_by=self.superuser,
            expires_at=timezone.now() - timedelta(days=1),
            is_active=True,
        )

        # Create an inactive token
        self.inactive_token = StaffEnrollmentToken.objects.create(
            token="inactive_test_token_789",
            created_by=self.superuser,
            expires_at=timezone.now() + timedelta(days=7),
            is_active=False,
        )

    def tearDown(self) -> None:
        """Clean up after tests"""
        cache.clear()

    def test_validate_token_valid(self) -> None:
        """Test validating a valid enrollment token"""
        response = self.client.post(
            "/api/user/staff-enrollment/validate-token",
            data=json.dumps({"token": self.valid_token.token}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["valid"])
        self.assertIn("expires_at", data)
        self.assertEqual(data["created_by"], self.superuser.username)

    def test_validate_token_invalid(self) -> None:
        """Test validating a non-existent token"""
        response = self.client.post(
            "/api/user/staff-enrollment/validate-token",
            data=json.dumps({"token": "nonexistent_token"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn("Invalid enrollment token", response.content.decode())

    def test_validate_token_expired(self) -> None:
        """Test validating an expired token"""
        response = self.client.post(
            "/api/user/staff-enrollment/validate-token",
            data=json.dumps({"token": self.expired_token.token}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("expired", response.content.decode())

    def test_validate_token_inactive(self) -> None:
        """Test validating an inactive token"""
        response = self.client.post(
            "/api/user/staff-enrollment/validate-token",
            data=json.dumps({"token": self.inactive_token.token}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("deactivated", response.content.decode())

    @patch("email_app.emails.send_signup_code_email")
    def test_staff_begin_signup_success(self, mock_send_email: Any) -> None:
        """Test beginning staff signup with valid token"""
        response = self.client.post(
            "/api/user/staff-enrollment/begin-signup",
            data=json.dumps(
                {
                    "enrollment_token": self.valid_token.token,
                    "email": "newstaff@example.com",
                    "password": "StrongPass123!",
                    "first_name": "New",
                    "last_name": "Staff",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        # Should return a JWT token
        jwt_token = response.content.decode().strip('"')
        self.assertIsNotNone(jwt_token)
        self.assertTrue(len(jwt_token) > 50)

        # Verify email was sent
        mock_send_email.assert_called_once()

        # Verify data is stored in cache
        cache_key = "staff-signup-data-newstaff@example.com"
        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data["email"], "newstaff@example.com")

    def test_staff_begin_signup_invalid_token(self) -> None:
        """Test beginning signup with invalid enrollment token"""
        response = self.client.post(
            "/api/user/staff-enrollment/begin-signup",
            data=json.dumps(
                {
                    "enrollment_token": "invalid_token",
                    "email": "newstaff@example.com",
                    "password": "StrongPass123!",
                    "first_name": "New",
                    "last_name": "Staff",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)

    def test_staff_begin_signup_expired_token(self) -> None:
        """Test beginning signup with expired enrollment token"""
        response = self.client.post(
            "/api/user/staff-enrollment/begin-signup",
            data=json.dumps(
                {
                    "enrollment_token": self.expired_token.token,
                    "email": "newstaff@example.com",
                    "password": "StrongPass123!",
                    "first_name": "New",
                    "last_name": "Staff",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    @patch("email_app.emails.send_signup_code_email")
    def test_staff_begin_signup_weak_password(self, mock_send_email: Any) -> None:
        """Test beginning signup with weak password"""
        response = self.client.post(
            "/api/user/staff-enrollment/begin-signup",
            data=json.dumps(
                {
                    "enrollment_token": self.valid_token.token,
                    "email": "newstaff@example.com",
                    "password": "weak",
                    "first_name": "New",
                    "last_name": "Staff",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 415)

    @patch("email_app.emails.send_signup_code_email")
    def test_staff_begin_signup_existing_user(self, mock_send_email: Any) -> None:
        """Test beginning signup with existing email"""
        # Create existing user
        User.objects.create_user(
            username="existing@example.com",
            email="existing@example.com",
            password="ExistingPass123!",
        )

        response = self.client.post(
            "/api/user/staff-enrollment/begin-signup",
            data=json.dumps(
                {
                    "enrollment_token": self.valid_token.token,
                    "email": "existing@example.com",
                    "password": "StrongPass123!",
                    "first_name": "New",
                    "last_name": "Staff",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 415)

    @patch("email_app.emails.send_signup_code_email")
    def test_staff_complete_signup_success(self, mock_send_email: Any) -> None:
        """Test completing staff signup with valid code"""
        # First, begin the signup
        email = "completesignup@example.com"
        password = "CompletePass123!"

        # Mock the verification code
        code = "123456"
        salt = "test_salt"

        # Store signup data in cache
        cache.set(
            f"staff-signup-data-{email}",
            {
                "email": email,
                "password": password,
                "first_name": "Complete",
                "last_name": "Signup",
                "food_preferences": None,
            },
            timeout=600,
        )

        # Create verification JWT
        verification_token = jwt_encode(
            {
                "code2fa": sha256(
                    (SECRET_KEY + salt + code).encode("utf-8"), usedforsecurity=True
                ).hexdigest(),
                "salt2fa": salt,
                "signup-data-hash": "test_hash",
            }
        )

        response = self.client.post(
            "/api/user/staff-enrollment/complete-signup",
            data=json.dumps(
                {
                    "enrollment_token": self.valid_token.token,
                    "verification_token": verification_token,
                    "code": code,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        # Verify user was created with staff privileges
        user = User.objects.get(email=email)
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_student)
        self.assertEqual(user.first_name, "Complete")

        # Verify enrollment usage was tracked
        usage = StaffEnrollmentUsage.objects.filter(
            token=self.valid_token,
            user=user,
        ).first()
        self.assertIsNotNone(usage)

        # Verify cache was cleared
        cached_data = cache.get(f"staff-signup-data-{email}")
        self.assertIsNone(cached_data)

    def test_staff_complete_signup_invalid_token(self) -> None:
        """Test completing signup with invalid enrollment token"""
        response = self.client.post(
            "/api/user/staff-enrollment/complete-signup",
            data=json.dumps(
                {
                    "enrollment_token": "invalid_token",
                    "verification_token": "some_jwt",
                    "code": "123456",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)

    def test_staff_complete_signup_wrong_code(self) -> None:
        """Test completing signup with wrong verification code"""
        email = "wrongcode@example.com"

        # Store signup data
        cache.set(
            f"staff-signup-data-{email}",
            {
                "email": email,
                "password": "WrongCodePass123!",
                "first_name": "Wrong",
                "last_name": "Code",
                "food_preferences": None,
            },
            timeout=600,
        )

        # Create verification JWT with different code
        salt = "test_salt"
        verification_token = jwt_encode(
            {
                "code2fa": sha256(
                    (SECRET_KEY + salt + "654321").encode("utf-8"), usedforsecurity=True
                ).hexdigest(),
                "salt2fa": salt,
                "signup-data-hash": "test_hash",
            }
        )

        response = self.client.post(
            "/api/user/staff-enrollment/complete-signup",
            data=json.dumps(
                {
                    "enrollment_token": self.valid_token.token,
                    "verification_token": verification_token,
                    "code": "123456",  # Wrong code
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid verification code", response.content.decode())

    def test_staff_complete_signup_expired_session(self) -> None:
        """Test completing signup with expired cache session"""
        salt = "test_salt"
        code = "123456"

        verification_token = jwt_encode(
            {
                "code2fa": sha256(
                    (SECRET_KEY + salt + code).encode("utf-8"), usedforsecurity=True
                ).hexdigest(),
                "salt2fa": salt,
                "signup-data-hash": "test_hash",
            }
        )

        # Don't store anything in cache to simulate expiration

        response = self.client.post(
            "/api/user/staff-enrollment/complete-signup",
            data=json.dumps(
                {
                    "enrollment_token": self.valid_token.token,
                    "verification_token": verification_token,
                    "code": code,
                }
            ),
            content_type="application/json",
        )

        # Should fail because email not in JWT
        self.assertEqual(response.status_code, 401)

    @patch("email_app.emails.send_signup_code_email")
    def test_multiple_users_same_token(self, mock_send_email: Any) -> None:
        """Test that the same enrollment token can be used multiple times"""
        # Create first user
        email1 = "staffuser1@example.com"
        password1 = "StaffPass123!"
        code1 = "123456"
        salt1 = "salt1"

        cache.set(
            f"staff-signup-data-{email1}",
            {
                "email": email1,
                "password": password1,
                "first_name": "Staff",
                "last_name": "One",
                "food_preferences": None,
            },
            timeout=600,
        )

        verification_token1 = jwt_encode(
            {
                "code2fa": sha256(
                    (SECRET_KEY + salt1 + code1).encode("utf-8"), usedforsecurity=True
                ).hexdigest(),
                "salt2fa": salt1,
                "signup-data-hash": "hash1",
            }
        )

        response1 = self.client.post(
            "/api/user/staff-enrollment/complete-signup",
            data=json.dumps(
                {
                    "enrollment_token": self.valid_token.token,
                    "verification_token": verification_token1,
                    "code": code1,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response1.status_code, 200)

        # Create second user with same token
        email2 = "staffuser2@example.com"
        password2 = "StaffPass456!"
        code2 = "654321"
        salt2 = "salt2"

        cache.set(
            f"staff-signup-data-{email2}",
            {
                "email": email2,
                "password": password2,
                "first_name": "Staff",
                "last_name": "Two",
                "food_preferences": None,
            },
            timeout=600,
        )

        verification_token2 = jwt_encode(
            {
                "code2fa": sha256(
                    (SECRET_KEY + salt2 + code2).encode("utf-8"), usedforsecurity=True
                ).hexdigest(),
                "salt2fa": salt2,
                "signup-data-hash": "hash2",
            }
        )

        response2 = self.client.post(
            "/api/user/staff-enrollment/complete-signup",
            data=json.dumps(
                {
                    "enrollment_token": self.valid_token.token,
                    "verification_token": verification_token2,
                    "code": code2,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response2.status_code, 200)

        # Verify both users exist and are staff
        user1 = User.objects.get(email=email1)
        user2 = User.objects.get(email=email2)

        self.assertTrue(user1.is_staff)
        self.assertTrue(user2.is_staff)

        # Verify both usages are tracked
        usages = StaffEnrollmentUsage.objects.filter(token=self.valid_token)
        self.assertEqual(usages.count(), 2)

    def test_token_usage_count(self) -> None:
        """Test that token usage count is correctly tracked"""
        # Create a user with the token
        user = User.objects.create_user(
            username="trackingtest@example.com",
            email="trackingtest@example.com",
            password="TrackingPass123!",
            is_staff=True,
            is_student=False,
        )

        StaffEnrollmentUsage.objects.create(
            token=self.valid_token,
            user=user,
        )

        # Check usage count
        self.assertEqual(self.valid_token.usages.count(), 1)

        # Validate token should still work (token is reusable)
        response = self.client.post(
            "/api/user/staff-enrollment/validate-token",
            data=json.dumps({"token": self.valid_token.token}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
