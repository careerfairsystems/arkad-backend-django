from django.http import HttpRequest


def get_base_url(request: HttpRequest) -> str:
    """
    Get the base URL from the request.
    """
    return request.build_absolute_uri("/")[:-1]


def get_base_url_from_settings() -> str:
    """
    Get the base URL from settings.
    """
    return "https://backend.arkadtlth.se"
