#from arkad.celery import app
from celery import shared_task
from event_booking.models import Event
from student_sessions.models import StudentSession, StudentSessionTimeslot
from user_models.models import User

# These are the tasks ot send notifications that are scheduled by scheduler.py


@shared_task
def notify_event_tmrw(user: User, event_name: str):
    pass


@shared_task
def notify_event_one_hour(user: User, event: Event | StudentSessionTimeslot):
    pass


@shared_task
def notify_event_reg_open(event: Event | StudentSession):
    # Both for lunch lectures, company visits (events?), and Student sessions
    #Anmälan för lunchföreläsning med XXX har öppnat -Bara notis
    # Anmälan för företagsbesök med XXX har öppnat - Bara notis
    pass


@shared_task
def notify_reg_close_tmrw(event: Event | StudentSession):
    # Defence companies (SAAB and FMV, any more?), append "swedish citizenship required"
    pass


@shared_task
def notify_appl_accept(user: User, event: Event | StudentSession):
    # Notify that a user has gotten their application accepted
    # Not a scheduled notification - this is triggered
    pass
