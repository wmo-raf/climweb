"""
WSGI config for nmhs_cms project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import os
import environ

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False),
)

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(PROJECT_DIR)

if os.path.exists(os.path.join(BASE_DIR, '.env')):
    # reading .env file
    environ.Env.read_env(os.path.join(BASE_DIR, '.env'))


from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"nmhs_cms.settings.{env.str('ENVIRONMENT', 'production')}")

application = get_wsgi_application()
