from .base import *

DEBUG = True
SECRET_KEY = "django-insecure-5=&i=f&w$_2=ktbhw43anl(uxgue*-i23r!1uibrh9l7-$q-1#"

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

MANIFEST_LOADER = {
    'cache': True,
    # recommended True for production, requires a server restart to pick up new values from the manifest.
}