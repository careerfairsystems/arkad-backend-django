from arkad.celery import app


@app.task(bind=True)
def check_notifications(self):  # type: ignore[no-untyped-def]
    print("Checking notifications!")


@app.task(bind=True)
def check_events_closing_within_24h(self):
    # Find all events with registration closing withing 24 hrs

    # for event in events
        # Notify all users about this
        # Anmälan för YYY med XXX stänger imorgon. Kom ihåg att avboka din plats om du inte kan komma!
        # Notis (+ Mail)
    pass


@app.task(bind=True)
def check_registered_events_tomorrow(self):
    # Run once daily?
    
    # Get all events that are tomorrow

    # for event in events
        # Get company
        # Find all users registered for that event
        # for user in users
            # Get their FCM token

            # Send notification
            # "Du har anmält dig till YYY med XXX är imorgon"
            # - notis ( + mail)

    pass


@app.task(bind=True)
def check_registered_events_in_one_hour(self):
    # Run hourly at every whole hour between 07-17?
    
    # Find get all events that are in within 1h 

    # for event in events
        # Get company
        # Find all users registered for that event

        # for user in users
            # Get their FCM token
            # Send notification
            # "Du har anmält dig till YYY som är med XXX är om en timme"
            # - Notis
    pass

