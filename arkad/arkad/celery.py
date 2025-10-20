import os
from celery import Celery  # type: ignore[import-untyped]

from arkad.settings import ENVIRONMENT

# Set default Django settings module for 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "arkad.settings")

app = Celery("arkad" if ENVIRONMENT == "production" else "arkad_staging")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix in Django settings.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):  # type: ignore[no-untyped-def]
    import time

    print(time.time())
