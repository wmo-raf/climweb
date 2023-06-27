from email.utils import getaddresses

from .base import *

try:
    from .local import *
except ImportError:
    pass

WAGTAIL_ENABLE_UPDATE_CHECK = False

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

DEBUG = env('DEBUG')

DATABASES = {
    'default': env.db()
}

INSTALLED_APPS = INSTALLED_APPS + [
    'wagtailcache'
]

MIDDLEWARE = MIDDLEWARE + [
    'wagtailcache.cache.UpdateCacheMiddleware',
    'wagtailcache.cache.FetchFromCacheMiddleware'
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, 'cache'),
        'KEY_PREFIX': 'nmhs_cms_default',
        'TIMEOUT': 14400,  # 4 hours (in seconds)
    },
    'pagecache': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': env('MEMCACHED_URI'),
        'KEY_PREFIX': 'nmhs_cms_pagecache',
        'TIMEOUT': 14400,  # 4 hours (in seconds)
    },
}

MANIFEST_LOADER = {
    'cache': True,
    # recommended True for production, requires a server restart to pick up new values from the manifest.
}

WAGTAIL_CACHE_BACKEND = env.str('WAGTAIL_CACHE_BACKEND', default='pagecache')

# Enable caching in production
WAGTAIL_CACHE = True

# To send email from the server, we recommend django_sendmail_backend
# Or specify your own email backend such as an SMTP server.
# https://docs.djangoproject.com/en/3.0/ref/settings/#email-backend
# EMAIL_BACKEND = 'django_sendmail_backend.backends.EmailBackend'

# Default email address used to send messages from the website.
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")

# A list of people who get error notifications.
ADMINS = getaddresses([env('DJANGO_ADMINS')])

# A list in the same format as ADMINS that specifies who should get some content management errors
MANAGERS = ADMINS + getaddresses([env('DJANGO_MANAGERS')])

# A list in the same format as DEVELOPERS for receiving developer aimed messages
DEVELOPERS = getaddresses([env('DJANGO_APP_DEVELOPERS')])

# Email address used to send error messages to ADMINS.
SERVER_EMAIL = DEFAULT_FROM_EMAIL

FILE_UPLOAD_TEMP_DIR = os.path.join(BASE_DIR, 'tmp')

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = env.str('EMAIL_HOST_USER', default='webadmin@icpac.net')
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'timestamp': {
            'format': '{asctime} {levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'error.log',
            'formatter': 'timestamp',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'timestamp',
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', cast=None)
STATICFILES_STORAGE = "base.storage.ManifestStaticFilesStorageNotStrict"

SECURE_CROSS_ORIGIN_OPENER_POLICY = env.str("SECURE_CROSS_ORIGIN_OPENER_POLICY", None)
