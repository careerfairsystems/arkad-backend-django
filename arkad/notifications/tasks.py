from notifications import handlers
from arkad.celery import app


@app.task(bind=True)
def schedule_notification_event_registration_in_24h(self):
    #handlers.send_event_one_hour()
    # Run every 48h at 12:00
    # Find all events with registration closing within 48 hours
    # with spots available

    # for event in events
        # find all users
        # Schedule a task to send a notification to all users at closing time - 24 hours

        # Anmälan för YYY med XXX stänger imorgon. Kom ihåg att avboka din plats om du inte kan komma!
        # Notis (+ Mail)
    pass


@app.task(bind=True)
def schedule_notification_event_tomorrow(self):
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
def schedule_notification_event_in_one_hour(self):
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

