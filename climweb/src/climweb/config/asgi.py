import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.conf import settings
from django.core.asgi import get_asgi_application
from django.urls import re_path, path
from django_nextjs.proxy import NextJSProxyHttpConsumer, NextJSProxyWebsocketConsumer

from climweb.config.telemetry.telemetry import setup_telemetry, setup_logging

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "climweb.config.settings.production")

# The telemetry instrumentation library setup needs to run prior to django's setup.
setup_telemetry(add_django_instrumentation=True)

django_asgi_app = get_asgi_application()

# It is critical to setup our own logging after django has been setup and done its own
# logging setup. Otherwise Django will try to destroy and log handlers we added prior.
setup_logging()

http_routes = [re_path(r"", django_asgi_app)]
websocket_routers = []

if settings.DEBUG:
    http_routes.insert(0, re_path(r"^(?:_next|__next|next).*", NextJSProxyHttpConsumer.as_asgi()))
    websocket_routers.insert(0, path("_next/webpack-hmr", NextJSProxyWebsocketConsumer.as_asgi()))

application = ProtocolTypeRouter(
    {
        # Django's ASGI application to handle traditional HTTP and websocket requests.
        "http": URLRouter(http_routes),
        "websocket": AuthMiddlewareStack(URLRouter(websocket_routers)),
    }
)
