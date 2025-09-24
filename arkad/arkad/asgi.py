"""
ASGI config for arkad project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from arkad.settings import DEBUG

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "arkad.settings")

from channels.auth import AuthMiddlewareStack  # type: ignore[import-untyped]
from channels.routing import ProtocolTypeRouter, URLRouter  # type: ignore[import-untyped]
from channels.security.websocket import AllowedHostsOriginValidator  # type: ignore[import-untyped]
from django.core.asgi import get_asgi_application


django_asgi_app = get_asgi_application()
from arkad import routing  # noqa: E402

asgi_settings = {
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(URLRouter(routing.websocket_urlpatterns))
    ),
}

if not DEBUG:
    del asgi_settings["http"]  # In production, we don't want to serve HTTP via ASGI

application = ProtocolTypeRouter(asgi_settings)
