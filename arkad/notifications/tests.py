from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings

from .models import Notification


@override_settings(DEBUG=True)
class NotificationModelTests(TestCase):
    def setUp(self) -> None:
        # Minimal user
        User = get_user_model()
        self.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="password123",
            first_name="Alice",
            last_name="Anderson",
        )

    def test_create_with_target_user_valid_when_auto_send_off(self) -> None:
        n = Notification.objects.create(
            target_user=self.user,
            title="Hello",
            body="Message body",
            # Intentionally set to True to verify they are not mutated when auto send is disabled
            email_sent=True,
            fcm_sent=True,
            auto_send_on_create=False,
        )

        self.assertIsNotNone(n.id)
        self.assertEqual(n.target_user, self.user)
        self.assertIsNone(n.notification_topic)
        # No sending should have occurred and flags should remain as initially set
        self.assertTrue(n.email_sent)
        self.assertTrue(n.fcm_sent)
        # sent_at should be auto-populated
        self.assertIsNotNone(n.sent_at)

        # __str__ should include the user and timestamp
        s = str(n)
        self.assertIn("Notification to", s)
        self.assertIn("Alice", s)

    def test_create_with_topic_valid_when_auto_send_off(self) -> None:
        n = Notification.objects.create(
            notification_topic="general-updates",
            title="Topic Title",
            body="Topic Body",
            auto_send_on_create=False,
        )

        self.assertIsNotNone(n.id)
        self.assertIsNone(n.target_user)
        self.assertEqual(n.notification_topic, "general-updates")
        # Defaults should be False
        self.assertFalse(n.email_sent)
        self.assertFalse(n.fcm_sent)
        self.assertIsNotNone(n.sent_at)

        s = str(n)
        self.assertIn("general-updates", s)

    def test_constraint_disallows_both_user_and_topic(self) -> None:
        n = Notification(
            target_user=self.user,
            notification_topic="dup",
            title="Invalid",
            body="Invalid",
            auto_send_on_create=False,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                n.save()

    def test_constraint_disallows_neither_user_nor_topic(self) -> None:
        n = Notification(
            title="Invalid",
            body="Invalid",
            auto_send_on_create=False,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                n.save()
