from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from django.contrib.auth import get_user_model
from django.db import connections
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature

from person_counter.models import PersonCounter, RoomModel

User = get_user_model()


class PersonCounterModelTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
            first_name="Test",
            last_name="User",
            username="testuser",
        )
        self.room = RoomModel.objects.create(name="hall-a")

    def test_sequential_add_delta_creates_snapshots(self) -> None:
        # initial: 0 -> +1 -> +2 -> -3 => final 0
        s1 = PersonCounter.add_delta(self.room, 1, updated_by=self.user)
        self.assertEqual(s1.count, 1)
        self.assertEqual(s1.delta, 1)

        s2 = PersonCounter.add_delta(self.room, 2, updated_by=self.user)
        self.assertEqual(s2.count, 3)
        self.assertEqual(s2.delta, 2)

        s3 = PersonCounter.add_delta(self.room, -3, updated_by=self.user)
        self.assertEqual(s3.count, 0)
        self.assertEqual(s3.delta, -3)

        last = PersonCounter.get_last(self.room.name)
        self.assertIsNotNone(last)
        assert last is not None
        self.assertEqual(last.count, 0)

    def test_reset_to_zero_creates_correct_delta(self) -> None:
        PersonCounter.add_delta(self.room, 5, updated_by=self.user)
        reset_row = PersonCounter.reset_to_zero(self.room, updated_by=self.user)
        self.assertEqual(reset_row.count, 0)
        self.assertEqual(reset_row.delta, -5)

    def test_reset_to_zero_at_zero_is_noop_snapshot(self) -> None:
        # When already zero, still create a no-op snapshot (delta 0) for traceability
        reset_row = PersonCounter.reset_to_zero(self.room, updated_by=self.user)
        self.assertEqual(reset_row.count, 0)
        self.assertEqual(reset_row.delta, 0)

    def test_get_last_returns_latest_by_created_at(self) -> None:
        PersonCounter.add_delta(self.room, 1, updated_by=self.user)
        PersonCounter.add_delta(self.room, 2, updated_by=self.user)
        last = PersonCounter.get_last(self.room.name)
        self.assertIsNotNone(last)
        assert last is not None
        self.assertEqual(last.count, 3)


class PersonCounterConcurrencyTests(TransactionTestCase):
    reset_sequences = True  # ensure predictable IDs across DB backends

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="conc@example.com",
            password="password123",
            first_name="Conc",
            last_name="User",
            username="concuser",
        )
        self.room = RoomModel.objects.create(name="hall-b")

    def tearDown(self) -> None:
        # Make sure background threads don’t keep connections open
        connections.close_all()

    def _worker(self, n: int, fn: Callable[[], None]) -> None:
        try:
            for _ in range(n):
                fn()
        finally:
            # Ensure each thread closes its DB connection when done
            connections.close_all()

    def _inc_once(self) -> None:
        PersonCounter.add_delta(self.room, 1, updated_by=self.user)

    @skipUnlessDBFeature("has_select_for_update")
    def test_concurrent_increments_are_atomic(self) -> None:
        # Only reliable on backends with real row-level locking (e.g., PostgreSQL)
        workers = 10
        per_worker = 10
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(self._worker, per_worker, self._inc_once) for _ in range(workers)]
            for f in as_completed(futures):
                f.result()

        last = PersonCounter.get_last(self.room.name)
        self.assertIsNotNone(last)
        assert last is not None
        self.assertEqual(last.count, workers * per_worker)
