"""
WSGI config for nmhs_cms project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from climweb.config.telemetry.telemetry import setup_telemetry, setup_logging

os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"climweb.config.settings.production")

# The telemetry instrumentation library setup needs to run prior to django's setup.
setup_telemetry(add_django_instrumentation=True)

application = get_wsgi_application()

# It is critical to setup our own logging after django has been setup and done its own
# logging setup. Otherwise Django will try to destroy and log handlers we added prior.
setup_logging()
