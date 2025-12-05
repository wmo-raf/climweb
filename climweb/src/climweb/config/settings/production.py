from .base import *

try:
    from .local import *
except ImportError:
    pass

WAGTAIL_ENABLE_UPDATE_CHECK = False

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

MANIFEST_LOADER = {
    'cache': True,
    # recommended True for production, requires a server restart to pick up new values from the manifest.
}

# Enable caching in production
WAGTAIL_CACHE = True

FILE_UPLOAD_TEMP_DIR = env.str("FILE_UPLOAD_TEMP_DIR", None)
if FILE_UPLOAD_TEMP_DIR is None or not os.path.exists(FILE_UPLOAD_TEMP_DIR):
    FILE_UPLOAD_TEMP_DIR = "/climweb/tmp"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env.str('EMAIL_HOST', default="localhost")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", False)
EMAIL_PORT = os.getenv("EMAIL_PORT", "")
if not EMAIL_PORT:
    EMAIL_PORT = 25
else:
    EMAIL_PORT = env.int('EMAIL_PORT', default=25)

EMAIL_HOST_USER = env.str('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD', default="")

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', cast=None, default=[])
SECURE_CROSS_ORIGIN_OPENER_POLICY = env.str("SECURE_CROSS_ORIGIN_OPENER_POLICY", None)

CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', cast=None, default=[])

# locales paths in production
if 'LOCALE_PATHS' in globals():
    LOCALE_PATHS = [
        p.replace('climweb/', '', 1) if p.startswith('climweb/') else p
        for p in LOCALE_PATHS
    ]