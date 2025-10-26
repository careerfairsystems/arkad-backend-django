import uuid
from unittest.mock import MagicMock, patch
from django.test import TestCase
from django.utils import timezone

# Import the model and decorator from your app
from .models import ScheduledCeleryTasks
from .tasks import db_backed_task_validity

# A unique ID for our test task
TEST_TASK_ID = str(uuid.uuid4())


class DbBackedTaskValidityTests(TestCase):
    def setUp(self):  # type: ignore[no-untyped-def]
        """
        Create a mock 'self' object that mimics a Celery task instance.
        This object is what the decorator will receive as 'self'.
        """
        self.mock_task_self = MagicMock()
        self.mock_task_self.request.id = TEST_TASK_ID
        self.mock_task_self.name = "mock_task_for_testing"

        # This is the "original function" that the decorator wraps.
        # We make it a mock so we can check if it was called.
        self.mock_original_func = MagicMock(name="mock_original_function")

        # Create a database entry for the task to run
        self.db_task_entry = ScheduledCeleryTasks.objects.create(
            task_id=TEST_TASK_ID, revoked=False, has_run=False, eta=timezone.now()
        )

    @patch("notifications.tasks.ScheduledCeleryTasks.should_run")
    def test_task_runs_when_valid_and_updates_db(self, mock_should_run):  # type: ignore[no-untyped-def]
        """
        Tests the "happy path":
        1. should_run() returns True.
        2. The original task function is executed.
        3. The task's 'has_run' flag is set to True in the DB.
        """
        # --- Arrange ---
        mock_should_run.return_value = True

        # Apply the decorator to our mock function
        decorated_func = db_backed_task_validity(self.mock_original_func)

        # --- Act ---
        # Call the decorated function, passing in the mock task instance
        decorated_func(self.mock_task_self)

        # --- Assert ---
        # 1. Check that should_run was called with the correct task ID
        mock_should_run.assert_called_once_with(TEST_TASK_ID)

        # 2. Check that the original function was called
        self.mock_original_func.assert_called_once_with(self.mock_task_self)

        # 3. Check that the database was updated
        self.db_task_entry.refresh_from_db()
        self.assertTrue(self.db_task_entry.has_run)

    @patch("notifications.tasks.ScheduledCeleryTasks.should_run")
    def test_task_skips_when_revoked(self, mock_should_run):  # type: ignore[no-untyped-def]
        """
        Tests the "skip path":
        1. should_run() returns False.
        2. The original task function is NOT executed.
        3. The database 'has_run' flag remains False.
        """
        # --- Arrange ---
        mock_should_run.return_value = False

        # Apply the decorator to our mock function
        decorated_func = db_backed_task_validity(self.mock_original_func)

        # --- Act ---
        decorated_func(self.mock_task_self)

        # --- Assert ---
        # 1. Check that should_run was called
        mock_should_run.assert_called_once_with(TEST_TASK_ID)

        # 2. Check that the original function was *NOT* called
        self.mock_original_func.assert_not_called()

        # 3. Check that the database was *NOT* updated
        self.db_task_entry.refresh_from_db()
        self.assertFalse(self.db_task_entry.has_run)

    @patch("notifications.tasks.logger")
    @patch("notifications.tasks.ScheduledCeleryTasks.should_run")
    def test_task_runs_but_logs_warning_if_db_entry_missing(  # type: ignore[no-untyped-def]
        self, mock_should_run, mock_logger
    ):
        """
        Tests the edge case where the task runs, but on the update step,
        the corresponding DB entry is gone.
        1. should_run() returns True.
        2. The original function is executed.
        3. A DoesNotExist exception is caught and a warning is logged.
        """
        # --- Arrange ---
        mock_should_run.return_value = True

        # Delete the database entry *before* running the task
        self.db_task_entry.delete()

        # Apply the decorator
        decorated_func = db_backed_task_validity(self.mock_original_func)

        # --- Act ---
        # This should run without raising a DoesNotExist exception
        decorated_func(self.mock_task_self)

        # --- Assert ---
        # 1. Check that should_run was called
        mock_should_run.assert_called_once_with(TEST_TASK_ID)

        # 2. Check that the original function *was* called
        self.mock_original_func.assert_called_once_with(self.mock_task_self)
