from user_models.models import User
from event_booking.models import Event

# These are the tasks ot send notifications that are scheduled by scheduler.py

def send_registration_closing_tomorrow(event: Event):
    # Defence companies (SAAB and FMV, any more?), append "only for swedish students"
    pass


def send_event_tomorrow(user: User, event: Event):
    pass


def send_event_one_hour(user: User, event: Event):
    # token = user.fcm_token
    pass

def send_lunch_registration_open(event: Event):
    pass
