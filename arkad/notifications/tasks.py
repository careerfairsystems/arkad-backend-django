from arkad.celery import app # type: ignore[import-untyped]


@app.task(bind=True)
def check_notifications(self):  # type: ignore[no-untyped-def]
    print("Checking notifications!")
