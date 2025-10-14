import os
from celery import Celery  # type: ignore[import-untyped]
from arkad.settings import DEBUG

# Set default Django settings module for 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "arkad.settings")

app = Celery("arkad")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix in Django settings.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# --- Patch apply_async to add scheduling logging ---
import logging
from datetime import datetime, timedelta, timezone
from functools import wraps

_logger = logging.getLogger("celery.schedule")
# Ensure INFO level for our scheduling messages
if _logger.level == logging.NOTSET or _logger.level > logging.INFO:
    _logger.setLevel(logging.INFO)

# Keep a reference so we only patch once (idempotent)
if not getattr(app.Task, "_apply_async_logging_patched", False) and DEBUG:  # type: ignore[attr-defined]
    _original_apply_async = app.Task.apply_async  # type: ignore[assignment]

    @wraps(_original_apply_async)  # type: ignore[misc]
    def _logging_apply_async(self, args=None, kwargs=None, task_id=None, producer=None, link=None, link_error=None, shadow=None, **options):  # type: ignore[no-untyped-def]
        # Determine scheduled time (eta or countdown) for logging purposes
        eta = options.get("eta")
        countdown = options.get("countdown")
        scheduled_for: datetime | None
        if eta is not None:
            # Celery may pass eta as aware datetime already
            if isinstance(eta, datetime):
                scheduled_for = eta
            else:  # fallback if mis-specified
                try:
                    scheduled_for = datetime.fromisoformat(str(eta))
                except Exception:  # noqa: BLE001
                    scheduled_for = None
        elif countdown is not None:
            try:
                scheduled_for = datetime.now(timezone.utc) + timedelta(seconds=float(countdown))
            except Exception:  # noqa: BLE001
                scheduled_for = None
        else:
            # Immediate execution (send to broker now)
            scheduled_for = datetime.now(timezone.utc)

        # Log BEFORE sending so logging still happens if broker send fails
        try:
            _logger.info(
                "Scheduling task name=%s provided_task_id=%s eta=%s countdown=%s queue=%s routing_key=%s args=%s kwargs_keys=%s",  # noqa: E501
                self.name,
                task_id,
                scheduled_for.isoformat() if scheduled_for else None,
                countdown,
                options.get("queue"),
                options.get("routing_key"),
                args,
                list(kwargs.keys()) if kwargs else None,
            )
        except Exception:  # noqa: BLE001
            pass

        return _original_apply_async(
            self,
            args=args,
            kwargs=kwargs,
            task_id=task_id,
            producer=producer,
            link=link,
            link_error=link_error,
            shadow=shadow,
            **options,
        )

    app.Task.apply_async = _logging_apply_async  # type: ignore[method-assign]
    setattr(app.Task, "_apply_async_logging_patched", True)  # type: ignore[arg-type]
    _logger.debug("Celery Task.apply_async patched for scheduling logging")
# --- End patch ---


@app.task(bind=True)
def debug_task(self):  # type: ignore[no-untyped-def]
    import time

    print(time.time())
