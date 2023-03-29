from .base import *

DEBUG = False

try:
    from .local import *
except ImportError:
    pass


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
        'KEY_PREFIX': 'nmhscms',
        'TIMEOUT': 14400, # one hour (in seconds)
    }
}
ALLOWED_HOSTS = [os.getenv('CMS_HOST'), 'localhost', '127.0.0.1'] 
