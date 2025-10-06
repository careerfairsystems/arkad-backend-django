from celery import shared_task  # type: ignore[import-untyped]

from arkad.celery import app


@shared_task
def notify_event_tmrw(user_id: int, event_id: int) -> None: # type: ignore[no-untyped-def]
    pass


@shared_task
def notify_event_one_hour(user_id: int, event_id: int) -> None: # type: ignore[no-untyped-def]
    pass


@shared_task
def notify_event_reg_open(event_id: int) -> None: # type: ignore[no-untyped-def]
    # Both for lunch lectures, company visits (events?), and Student sessions
    #Anmälan för lunchföreläsning med XXX har öppnat -Bara notis
    # Anmälan för företagsbesök med XXX har öppnat - Bara notis
    pass


@shared_task
def notify_reg_close_tmrw(event_id: int) -> None: # type: ignore[no-untyped-def]
    # Defence companies (SAAB and FMV, any more?), append "swedish citizenship required"
    pass


@shared_task
def notify_appl_accept(user_id: int, event_id: int) -> None:
    # Notify that a user has gotten their application accepted
    # Not a scheduled notification - this is triggered
    pass
