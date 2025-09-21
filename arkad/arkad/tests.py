import time

from django.test import TestCase
from arkad.jwt_utils import jwt_decode
from user_models.models import User


class TestJWT(TestCase):
    def test_expiry(self):
        user = User.objects.create_user(
            "test@test.com", email="test@test.com", password="<PASSWORD>"
        )
        token = user.create_jwt_token(expiry_days=30)
        exp = jwt_decode(token.split(" ")[1])["exp"]

        # Assert that the token has almost 30 days to expiry, allow 10s for clock skew
        self.assertAlmostEqual(exp, time.time() + 30 * 24 * 60 * 60, delta=10)


class TestCache(TestCase):
    def test_cache(self):
        from django.core.cache import cache

        cache.set("test_key", "test_value", timeout=1)
        value = cache.get("test_key")
        self.assertEqual(value, "test_value")
        time.sleep(1)
        value = cache.get("test_key")
        self.assertIsNone(value)
