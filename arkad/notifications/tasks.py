from celery import shared_task  # type: ignore[import-untyped]


@shared_task  # type: ignore
def notify_event_tomorrow(user_id: int, event_id: int) -> None:
    pass


@shared_task  # type: ignore
def notify_event_one_hour(user_id: int, event_id: int) -> None:
    pass


@shared_task  # type: ignore
def notify_event_registration_open(event_id: int) -> None:
    # Both for lunch lectures, company visits (events?), and Student sessions
    # Anmälan för lunchföreläsning med XXX har öppnat -Bara notis
    # Anmälan för företagsbesök med XXX har öppnat - Bara notis
    pass


@shared_task  # type: ignore
def notify_registration_closes_tomorrow(event_id: int) -> None:
    # Defence companies (SAAB and FMV, any more?), append "swedish citizenship required"
    pass


@shared_task  # type: ignore
def notify_application_accepted(user_id: int, event_id: int) -> None:
    # Notify that a user has gotten their application accepted
    # Not a scheduled notification - this is triggered
    pass
