from datetime import timedelta

from django.db import models
from django.utils import timezone

from arkad.celery import app
from notifications import tasks
from event_booking.models import Event
from student_sessions.models import StudentSession

# Tasks schedulers that schedule other tasks

@app.task(bind=True)
def schedule_notify_registration_opening(self):  # type: ignore[no-untyped-def]
    # Run every 48h at 12:00
    now = timezone.now()
    in_24h = now + timedelta(hours=24)
    # Find all events with registration opening within 24 hours with spots
    events = Event.objects.filter(
                release_time__gte=now, 
                release_time__lte=in_24h,
                number_booked__lt=models.F("capacity")
            )
    # Also for student sessions?

    # for event in events
    for event in events:
        pass
        # Schedule a task to send a notification to all users at closing time - 24 hours

        # Anmälan för YYY med XXX har öppnat
        # Notis (+ Mail)
    pass

@app.task(bind=True)
def schedule_notify_registration_closing(self):  # type: ignore[no-untyped-def]
    #handlers.send_event_one_hour()
    # Run every 48h at 12:00
    # Find all events with registration closing within 48 hours
    # with spots available

    # for event in events
        # Schedule a task to send a notification to all users at closing time - 24 hours

        # Anmälan för YYY med XXX stänger imorgon. Kom ihåg att avboka din plats om du inte kan komma!
        # Notis (+ Mail)
    pass


@app.task(bind=True)
def schedule_notify_event_tomorrow(self):  # type: ignore[no-untyped-def]
    # Run every other day?
    # Get all events that are within 48 hours

    # for event in events
        # Get company
        # Find all users registered for that event

        # for user in users
            
            # Get their FCM token
            # Schedule a task to send a notification to the user at event time minus 24 hours

            # "Du har anmält dig till YYY med XXX är imorgon" - notis ( + mail)

    pass


@app.task(bind=True)
def schedule_notify_event_in_one_hour(self):  # type: ignore[no-untyped-def]
    # Run every two hours between 07-17?
    # Find get all events that are in within 2h 

    # for event in events
        # Get company
        # Find all users registered for that event

        # for user in users
            # Get their FCM token
            # Send notification
            # Schedule a task to send a notification to the user at event time minus 1 hour
            # "Du har anmält dig till YYY som är med XXX är om en timme" - Notis
    pass

