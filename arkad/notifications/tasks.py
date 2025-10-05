from celery import shared_task


@shared_task
def notify_event_tmrw(user_id: int, event_id: int):
    pass


@shared_task
def notify_event_one_hour(user_id: int, event_id: int):
    pass


@shared_task
def notify_event_reg_open(event_id: int):
    # Both for lunch lectures, company visits (events?), and Student sessions
    #Anmälan för lunchföreläsning med XXX har öppnat -Bara notis
    # Anmälan för företagsbesök med XXX har öppnat - Bara notis
    pass


@shared_task
def notify_reg_close_tmrw(event_id: int):
    # Defence companies (SAAB and FMV, any more?), append "swedish citizenship required"
    pass


@shared_task
def notify_appl_accept(user_id: int, event_id: int):
    # Notify that a user has gotten their application accepted
    # Not a scheduled notification - this is triggered
    pass
