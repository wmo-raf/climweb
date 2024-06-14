from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

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
WAGTAIL_CACHE = env.bool('WAGTAIL_CACHE', default=False)

INSTALLED_APPS = ["daphne"] + INSTALLED_APPS + ["wagtail.contrib.styleguide"]

ASGI_APPLICATION = "nmhs_cms.asgi.application"

STATICFILES_STORAGE = "base.storage.ManifestStaticFilesStorageNotStrict"

SHOW_TOOLBAR_CALLBACK = False
SHOW_COLLAPSED = False

# used in dev with Mac OS
GDAL_LIBRARY_PATH = env.str('GDAL_LIBRARY_PATH', None)
GEOS_LIBRARY_PATH = env.str('GEOS_LIBRARY_PATH', None)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, 'cache'),
        'KEY_PREFIX': 'nmhs_cms_default',
        'TIMEOUT': 14400,  # 4 hours (in seconds)
    },
    'pagecache': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': env('MEMCACHED_URI', default=""),
        'KEY_PREFIX': 'nmhs_cms_pagecache',
        'TIMEOUT': 14400,  # 4 hours (in seconds)
    },
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        # Send logs with at least INFO level to the console.
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s][%(process)d][%(levelname)s][%(name)s] %(message)s"
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
