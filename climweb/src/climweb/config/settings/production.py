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
_resolved_locale_paths = []
_original_locale_paths = list(globals().get('LOCALE_PATHS', []))

for p in _original_locale_paths:
    # if already absolute and exists, keep it
    cand = Path(p)
    if cand.is_absolute() and cand.exists():
        _resolved_locale_paths.append(str(cand))
        continue

    # candidate 1: BASE_DIR / p
    cand1 = Path(BASE_DIR) / p
    if cand1.exists():
        _resolved_locale_paths.append(str(cand1))
        continue

    # candidate 2: if p starts with 'climweb/', try stripping it (dev -> prod fix)
    if str(p).startswith('climweb/'):
        cand2 = Path(BASE_DIR) / str(p).replace('climweb/', '', 1)
        if cand2.exists():
            _resolved_locale_paths.append(str(cand2))
            continue

    # candidate 3: try prepending 'src/' (in case p was 'climweb/src/...' vs desired 'src/...')
    cand3 = Path(BASE_DIR) / 'src' / Path(p).relative_to('climweb') if 'climweb' in str(p) else Path(BASE_DIR) / 'src' / p
    if cand3.exists():
        _resolved_locale_paths.append(str(cand3))
        continue

    # candidate 4: last resort - try BASE_DIR / 'climweb' / p (handles some layouts)
    cand4 = Path(BASE_DIR) / 'climweb' / p
    if cand4.exists():
        _resolved_locale_paths.append(str(cand4))
        continue

    # if none exists, keep the BASE_DIR/p candidate (helps surface path issues)
    _resolved_locale_paths.append(str(cand1))

# Deduplicate while preserving order
seen = set()
LOCALE_PATHS = []
for x in _resolved_locale_paths:
    if x not in seen:
        LOCALE_PATHS.append(x)
        seen.add(x)
