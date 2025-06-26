from django.http import HttpRequest


def get_base_url(request: HttpRequest) -> str:
    """
    Returns the base URL of the request, including the protocol and host.
    """
    if not request:
        raise ValueError("Request object is required to get the base URL.")

    if not hasattr(request, "is_secure") or not hasattr(request, "get_host"):
        raise ValueError("Request object must have 'is_secure' and 'get_host' methods.")
    protocol: str = "https" if request.is_secure() else "http"
    host: str = request.get_host()
    return f"{protocol}://{host}"
