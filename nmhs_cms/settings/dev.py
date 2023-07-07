from .base import *

import environ

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False),
)
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG', True)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-5=&i=f&w$_2=ktbhw43anl(uxgue*-i23r!1uibrh9l7-$q-1#"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

try:
    from .local import *
except ImportError:
    pass

# Disable caching in dev
WAGTAIL_CACHE = False

INSTALLED_APPS = INSTALLED_APPS + [
    'wagtail.contrib.styleguide'
]

STATICFILES_STORAGE = "base.storage.ManifestStaticFilesStorageNotStrict"

SHOW_TOOLBAR_CALLBACK = False
SHOW_COLLAPSED = False

# used in dev with Mac OS
GDAL_LIBRARY_PATH = env.str('GDAL_LIBRARY_PATH', None)
GEOS_LIBRARY_PATH = env.str('GEOS_LIBRARY_PATH', None)
