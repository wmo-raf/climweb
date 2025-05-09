"""
Django settings for climweb project
"""

import base64
import importlib
import os
from email.utils import getaddresses
from pathlib import Path

import dj_database_url
import django.conf.locale
import environ
from django.core.exceptions import ImproperlyConfigured
from signxml import SignatureMethod

from climweb import VERSION
from climweb.config.telemetry.utils import otel_is_enabled

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(PROJECT_DIR)

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False),
    EMAIL_USE_TLS=(bool, True),
)

dev_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(BASE_DIR))), ".env")

if os.path.isfile(dev_env_path):
    # reading .env file
    environ.Env.read_env(dev_env_path)

DEBUG = env('DEBUG', False)

# Application definition
INSTALLED_APPS = [
    "climweb.base",
    
    "climweb.pages.home",
    "climweb.pages.services",
    "climweb.pages.products",
    "climweb.pages.weather",
    "climweb.pages.mediacenter",
    "climweb.pages.news",
    "climweb.pages.videos",
    "climweb.pages.publications",
    "climweb.pages.contact",
    "climweb.pages.feedback",
    "climweb.pages.events",
    "climweb.pages.organisation_pages.organisation",
    "climweb.pages.organisation_pages.about",
    "climweb.pages.organisation_pages.partners",
    "climweb.pages.organisation_pages.projects",
    "climweb.pages.organisation_pages.tenders",
    "climweb.pages.organisation_pages.vacancies",
    "climweb.pages.organisation_pages.staff",
    "climweb.pages.email_subscription",
    "climweb.pages.surveys",
    "climweb.pages.search",
    "climweb.pages.data_request",
    "climweb.pages.flex_page",
    "climweb.pages.stations",
    "climweb.pages.satellite_imagery",
    "climweb.pages.cityclimate",
    "climweb.pages.glossary",
    "climweb.pages.webstories",
    "climweb.pages.wdqms",
    
    "adminboundarymanager",
    "geomanager",
    "alertwise.capeditor",
    "alertwise.cap",
    "forecastmanager",
    "climweb_wdqms",
    
    "wagtailmautic",
    "wagtailzoom",
    "wagtailsurveyjs",
    "wagtailmailchimp",
    "wagtailhumanitarianicons",
    "wagtailiconchooser",
    "wagtail_webstories_editor",
    "wagtailmedia",
    
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    'wagtail.contrib.settings',
    "wagtail.contrib.routable_page",
    'wagtail.contrib.search_promotions',
    "wagtail.contrib.table_block",
    'wagtail.contrib.sitemaps',
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    "wagtail.api.v2",
    
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    'django.contrib.sitemaps',
    'django.contrib.humanize',
    
    "modelcluster",
    "rest_framework",
    'rest_framework_xml',
    "taggit",
    "corsheaders",
    "wagtailcache",
    "allauth",
    "allauth.account",
    "wagtail_adminsortable",
    "wagtailmetadata",
    "wagtailfontawesomesvg",
    "wagtailgeowidget",
    "wagtail_lazyimages",
    "wagtail_color_panel",
    "django_large_image",
    'django_json_widget',
    'django_nextjs',
    "django_filters",
    "django_deep_translator",
    "widget_tweaks",
    "django_recaptcha",
    'wagtailcaptcha',
    "bulma",
    "mailchimp3",
    "manifest_loader",
    "django_tables2",
    "django_tables2_bulma_template",
    "django_cleanup",
    "django_countries",
    "wagtail_modeladmin",
    "dbbackup",
    "wagtailmodelchooser",
    "django_extensions",
    "django_celery_beat",
    "django_celery_results",
    "axes",
    'wagtail_2fa',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_vue_utilities',
    'wagtail_newsletter',
]

CLIMWEB_ADDITIONAL_APPS = env.list("CLIMWEB_ADDITIONAL_APPS", default=[])
if CLIMWEB_ADDITIONAL_APPS:
    print(f"Loaded ClimWeb additional apps: {','.join(CLIMWEB_ADDITIONAL_APPS)}")
    INSTALLED_APPS += CLIMWEB_ADDITIONAL_APPS

CLIMWEB_PLUGIN_DIR = env("CLIMWEB_PLUGIN_DIR", default="/climweb/plugins")
if CLIMWEB_PLUGIN_DIR and Path(CLIMWEB_PLUGIN_DIR).exists():
    climweb_plugin_dir_path = Path(CLIMWEB_PLUGIN_DIR)
    CLIMWEB_PLUGIN_FOLDERS = [file for file in climweb_plugin_dir_path.iterdir() if file.is_dir()]
else:
    CLIMWEB_PLUGIN_FOLDERS = []

CLIMWEB_PLUGIN_NAMES = [d.name for d in CLIMWEB_PLUGIN_FOLDERS]

if CLIMWEB_PLUGIN_NAMES:
    print(f"Loaded plugins: {','.join(CLIMWEB_PLUGIN_NAMES)}")
    INSTALLED_APPS.extend(CLIMWEB_PLUGIN_NAMES)

AUTHENTICATION_BACKENDS = [
    # AxesStandaloneBackend should be the first backend in the AUTHENTICATION_BACKENDS list.
    'axes.backends.AxesStandaloneBackend',
    
    # Django ModelBackend is the default authentication backend.
    'django.contrib.auth.backends.ModelBackend',
]

PO_TRANSLATOR_SERVICE = 'django_deep_translator.services.GoogleTranslatorService'
DEEPL_TRANSLATE_KEY = "testkey"
DEEPL_FREE_API = True

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    'django.middleware.locale.LocaleMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
    
    'wagtail_2fa.middleware.VerifyUserPermissionsMiddleware',
    
    # AxesMiddleware should be the last middleware in the MIDDLEWARE list.
    # It only formats user lockout messages and renders Axes lockout responses
    # on failed user authentication attempts from login views.
    # If you do not want Axes to override the authentication response
    # you can skip installing the middleware and use your own views.
    'axes.middleware.AxesMiddleware',
]

if otel_is_enabled():
    MIDDLEWARE += ["climweb.config.telemetry.middleware.OTELMiddleware"]

ROOT_URLCONF = "climweb.config.urls"
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(PROJECT_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                'django.template.context_processors.media',
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "wagtail.contrib.settings.context_processors.settings",
                'django.template.context_processors.i18n',
                'climweb.base.context_processors.theme',
                "django.template.context_processors.debug",
            ],
        },
    },
]

WSGI_APPLICATION = "climweb.config.wsgi.application"

ASGI_APPLICATION = "climweb.config.asgi.application"

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DB_ENGINE = "climweb.config.db_engine"

DB_CONNECTION_MAX_AGE = env.int("DB_CONNECTION_MAX_AGE", default=600)

DATABASES = {
    "default": dj_database_url.config(
        engine=DB_ENGINE,
        conn_max_age=DB_CONNECTION_MAX_AGE,
        conn_health_checks=True,
    )
}

DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {'location': os.path.join(BASE_DIR, "backup")}
DBBACKUP_CLEANUP_KEEP_MEDIA = 1
DBBACKUP_CLEANUP_KEEP = 1
DBBACKUP_CONNECTORS = {
    "default": {
        "CONNECTOR": "dbbackup.db.postgresql.PgDumpBinaryConnector",  # Use pg_dump binary
        "DUMP_SUFFIX": "-e plpgsql",  # dump only system extensions
        "RESTORE_SUFFIX": "--if-exists"  # Drop only if exists
    }
}

DBBACKUP_CONNECTOR_MAPPING = {
    DB_ENGINE: "dbbackup.db.postgresql.PgDumpBinaryConnector",
}

REST_FRAMEWORK = {
    # 'DEFAULT_RENDERER_CLASSES': (
    #     'rest_framework.renderers.JSONRenderer',
    # ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    ),
}

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/
LANGUAGE_CODE = env.str("LANGUAGE_CODE", default="en")

# add amharic to supported locale
EXTRA_LANG_INFO = {
    'am': {
        'bidi': False,
        'code': 'am',
        'name': 'Amharic',
        'name_local': "Amharic"
    },
}
# Add custom languages not provided by Django
LANG_INFO = dict(django.conf.locale.LANG_INFO, **EXTRA_LANG_INFO)
django.conf.locale.LANG_INFO = LANG_INFO

LANGUAGES = WAGTAIL_CONTENT_LANGUAGES = WAGTAILADMIN_PERMITTED_LANGUAGES = [
    ('am', 'Amharic'),
    ('ar', 'Arabic'),
    ('en', 'English'),
    ('es', 'Español'),
    ('fr', 'French'),
    ('sw', 'Swahili'),
]

LOCALE_PATHS = [
    'base/locale',
    'nmhs_cms/locale',
    
    'pages/cap/locale',
    'pages/cityclimate/locale',
    'pages/contact/locale',
    'pages/data_request/locale',
    'pages/email_subscription/locale',
    'pages/events/locale',
    'pages/feedback/locale',
    'pages/flex_page/locale',
    'pages/glossary/locale',
    'pages/home/locale',
    'pages/mediacenter/locale',
    'pages/news/locale',
    'pages/organisation_pages/about/locale',
    'pages/organisation_pages/organisation/locale',
    'pages/organisation_pages/partners/locale',
    'pages/organisation_pages/projects/locale',
    'pages/organisation_pages/tenders/locale',
    'pages/organisation_pages/vacancies/locale',
    'pages/organisation_pages/staff/locale',
    
    'pages/products/locale',
    'pages/publications/locale',
    'pages/satellite_imagery/locale',
    'pages/search/locale',
    'pages/services/locale',
    'pages/stations/locale',
    'pages/surveys/locale',
    'pages/videos/locale',
    'pages/wdqms/locale',
    'pages/weather/locale',
    'pages/webstories/locale',
]

# Add additional apps to locale paths
if "climweb.pages.aviation" in CLIMWEB_ADDITIONAL_APPS:
    LOCALE_PATHS.append('pages/aviation/locale')

TIME_ZONE = env.str("TIME_ZONE", "UTC")

USE_I18N = True
# WAGTAIL_I18N_ENABLED = True

USE_L10N = True

USE_TZ = True

WAGTAILADMIN_STATIC_FILE_VERSION_STRINGS = False

# Storages
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "climweb.base.storage.ManifestStaticFilesStorageNotStrict",
    },
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "django.contrib.staticfiles.finders.FileSystemFinder",
]

STATICFILES_DIRS = [
    os.path.join(PROJECT_DIR, "static"),
]

# ManifestStaticFilesStorage is recommended in production, to prevent outdated
# JavaScript / CSS assets being served from cache (e.g. after a Wagtail upgrade).
# See https://docs.djangoproject.com/en/4.0/ref/contrib/staticfiles/#manifeststaticfilesstorage
# STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = env.str("FORCE_SCRIPT_NAME", "") + "/static/"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = env.str("FORCE_SCRIPT_NAME", "") + "/media/"

# Wagtail settings
WAGTAIL_SITE_NAME = env.str("WAGTAIL_SITE_NAME", "ClimWeb")

# Search
# https://docs.wagtail.org/en/stable/topics/search/backends.html
WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "wagtail.search.backends.database",
    }
}

# Base URL to use when referring to full URLs within the Wagtail admin backend -
# e.g. in notification emails. Don't include '/admin' or a trailing slash
WAGTAILADMIN_BASE_URL = env.str('WAGTAILADMIN_BASE_URL', '')

GEO_WIDGET_DEFAULT_LOCATION = {
    'lng': 0,
    'lat': 0
}
GEO_WIDGET_EMPTY_LOCATION = False

GEO_WIDGET_ZOOM = 3

SUMMARY_RICHTEXT_FEATURES = ["bold", "ul", "ol", "link", "superscript", "subscript", "h2", "h3", "h4"]
FULL_RICHTEXT_FRATURES = ['bold', 'italic', 'underline', 'strikethrough', 'superscript', 'subscript',
                          'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'ol', 'ul', 'link', 'document-link',
                          'image', 'embed', 'hr', 'anchor', 'table', 'justifyLeft', 'justifyCenter', 'justifyRight',
                          'justifyFull', 'indent', 'outdent', 'html']
# RECAPTCHA Settings
RECAPTCHA_PUBLIC_KEY = env.str('RECAPTCHA_PUBLIC_KEY', '')
RECAPTCHA_PRIVATE_KEY = env.str('RECAPTCHA_PRIVATE_KEY', '')
# RECAPTCHA_DOMAIN = env.str('RECAPTCHA_DOMAIN', 'www.google.com')
RECAPTCHA_VERIFY_REQUEST_TIMEOUT = env.str('RECAPTCHA_VERIFY_REQUEST_TIMEOUT', "60")

# try to convert RECAPTCHA_VERIFY_REQUEST_TIMEOUT to an integer
if RECAPTCHA_VERIFY_REQUEST_TIMEOUT:
    try:
        RECAPTCHA_VERIFY_REQUEST_TIMEOUT = int(RECAPTCHA_VERIFY_REQUEST_TIMEOUT)
    except ValueError:
        RECAPTCHA_VERIFY_REQUEST_TIMEOUT = 60

# EMAIL SETTINGS
# Default email address used to send messages from the website.
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="")

# A list of people who get error notifications.
ADMINS = getaddresses([env('DJANGO_ADMINS', default="")])

# A list in the same format as ADMINS that specifies who should get some content management errors
MANAGERS = ADMINS + getaddresses([env('DJANGO_MANAGERS', default="")])

# A list in the same format as DEVELOPERS for receiving developer aimed messages
DEVELOPERS = getaddresses([env('DJANGO_APP_DEVELOPERS', default="")])

# Email address used to send error messages to ADMINS.
SERVER_EMAIL = DEFAULT_FROM_EMAIL

WAGTAILDOCS_DOCUMENT_MODEL = 'base.CustomDocumentModel'
WAGTAILEMBEDS_RESPONSIVE_HTML = True

# AUTH STUFF
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
ACCOUNT_LOGOUT_REDIRECT_URL = '/login/'
ACCOUNT_PRESERVE_USERNAME_CASING = False
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False
ACCOUNT_USERNAME_BLACKLIST = ["admin", "god", "superadmin", "staff"]
ACCOUNT_USERNAME_MIN_LENGTH = 3

ONLINE_SHARE_CONFIG = [
    {
        "name": "Facebook",
        "base_url": "https://www.facebook.com/sharer/sharer.php",
        "link_param": "u",
        "text_param": "quote",
        "fa_icon": "facebook-f",
        "enabled": True,
        "svg_icon": "facebook",
    },
    {
        "name": "X",
        "base_url": "https://twitter.com/intent/post",
        "link_param": "url",
        "text_param": "text",
        "fa_icon": "x-twitter",
        "svg_icon": "x-twitter",
        "enabled": True,
    },
    {
        "name": "LinkedIn",
        "base_url": "https://www.linkedin.com/sharing/share-offsite",
        "link_param": "url",
        "fa_icon": "linkedin-in",
        "svg_icon": "linkedin",
        "enabled": True,
    },
    {
        "name": "WhatsApp",
        "base_url": "https://api.whatsapp.com/send",
        "link_param": "text",
        "encode": True,
        "text_in_url": True,
        "fa_icon": "whatsapp",
        "svg_icon": "whatsapp",
        "enabled": True,
    },
    {
        "name": "Telegram",
        "base_url": "https://t.me/share/url",
        "link_param": "url",
        "text_param": "text",
        "fa_icon": "telegram",
        "svg_icon": "telegram",
        "enabled": True,
    },

]

CORS_ALLOW_ALL_ORIGINS = True

NEXTJS_SETTINGS = {
    "nextjs_server_url": env.str("NEXTJS_SERVER_URL", default=""),
}

FORCE_SCRIPT_NAME = env.str("FORCE_SCRIPT_NAME", default="")

WAGTAILIMAGES_EXTENSIONS = ["gif", "jpg", "jpeg", "png", "webp", "svg"]

DJANGO_TABLES2_TEMPLATE = "django-tables2/bulma.html"

ADMIN_URL_PATH = env.str("ADMIN_URL_PATH", "cms-admin")
DJANGO_ADMIN_URL_PATH = env.str("DJANGO_ADMIN_URL_PATH", default="dj-ad-admin")

CMS_UPGRADE_HOOK_URL = env.str("CMS_UPGRADE_HOOK_URL", default="")

WAGTAIL_WEBSTORIES_EDITOR_LISTING_PAGE_MODEL = "webstories.WebStoryListPage"

# GeoManager settings
GEOMANAGER_AUTO_INGEST_RASTER_DATA_DIR = env.str("GEOMANAGER_AUTO_INGEST_RASTER_DATA_DIR", "")
GEOMANAGER_EXTRA_NC_TIME_DIMENSION_NAMES = env.list("GEOMANAGER_EXTRA_NC_TIME_DIMENSION_NAMES", default=[])

USE_X_FORWARDED_HOST = env.bool("USE_X_FORWARDED_HOST", default=True)

DATA_UPLOAD_MAX_MEMORY_SIZE = env.int("DATA_UPLOAD_MAX_MEMORY_SIZE", default=26214400)  # 25MB

MBGL_RENDERER_URL = env.str("MBGL_RENDERER_URL", default="")

# CAP Composer Settings
CAP_CERT_PATH = env.str("CAP_CERT_PATH", default="")
CAP_PRIVATE_KEY_PATH = env.str("CAP_PRIVATE_KEY_PATH", default="")
CAP_SIGNATURE_METHOD = env.str("CAP_SIGNATURE_METHOD", default="RSA_SHA256")
CAP_MQTT_SECRET_KEY = env.str("CAP_MQTT_SECRET_KEY", default="")
CAP_LIST_PAGE_PARENT_PAGE_TYPES = ["home.HomePage", ]  # can only add CAPListPage the home page
MAX_CAP_LIST_PAGE_COUNT = 1  # can only have one CAPListPage

if CAP_MQTT_SECRET_KEY:
    try:
        base64.urlsafe_b64decode(CAP_MQTT_SECRET_KEY)
    except Exception as e:
        raise ImproperlyConfigured(f"CAP_MQTT_SECRET_KEY must be a base64 encoded string. {e}")
    
    if len(CAP_MQTT_SECRET_KEY) != 44:
        raise ImproperlyConfigured("CAP_MQTT_SECRET_KEY must be 44 characters long")

CAP_WIS2BOX_INTERNAL_TOPIC = env.str("CAP_WIS2BOX_INTERNAL_TOPIC", default="wis2box/cap/publication")

if CAP_SIGNATURE_METHOD:
    assert hasattr(SignatureMethod, CAP_SIGNATURE_METHOD), f"Invalid signature method '{CAP_SIGNATURE_METHOD}'. " \
                                                           f"Must be one of " \
                                                           f"{list(SignatureMethod.__members__.keys())}"
    CAP_SIGNATURE_METHOD = SignatureMethod[CAP_SIGNATURE_METHOD]

DEFAULT_WAGTAILIMAGES_EXTENSIONS = ['png', 'jpg', 'avif', 'gif', 'jpeg', 'webp']
WAGTAILIMAGES_EXTENSIONS = env.list("WAGTAILIMAGES_EXTENSIONS", default=DEFAULT_WAGTAILIMAGES_EXTENSIONS)

DEFAULT_WAGTAILDOCS_EXTENSIONS = ['pdf', 'docx', 'xlsx', 'pptx', 'csv', 'odt', 'rtf', 'txt', 'key', 'zip', 'doc']
WAGTAILDOCS_EXTENSIONS = env.list("WAGTAILDOCS_EXTENSIONS", default=DEFAULT_WAGTAILDOCS_EXTENSIONS)

CAP_ALLOW_EDITING = env.bool("CAP_ALLOW_EDITING", default=False)

REDIS_HOST = env.str("REDIS_HOST", "redis")
REDIS_PORT = env.str("REDIS_PORT", "6379")
REDIS_USERNAME = env.str("REDIS_USER", "")
REDIS_PASSWORD = env.str("REDIS_PASSWORD", "")
REDIS_PROTOCOL = env.str("REDIS_PROTOCOL", "redis")
REDIS_URL = env.str(
    "REDIS_URL",
    f"{REDIS_PROTOCOL}://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0",
)

CELERY_BROKER_URL = REDIS_URL
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_RESULT_BACKEND = "django-db"
CELERY_RESULT_EXTENDED = True
CELERY_CACHE_BACKEND = "default"

CELERY_SINGLETON_BACKEND_CLASS = (
    "climweb.celery_singleton_backend.RedisBackendForSingleton"
)

# Set max memory per child process (in kilobytes, e.g., 200000 KB = 200 MB)
CELERY_WORKER_MAX_MEMORY_PER_CHILD = env.int("CELERY_WORKER_MAX_MEMORY_PER_CHILD", default=200000)

CELERY_APP = 'climweb.config.celery:app'

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_PREFIX": "climweb-default-cache",
        "VERSION": VERSION,
        "TIMEOUT": 60 * 60 * 4,  # 4 hours
    },
}

# Django AXES settings
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]
AXES_IPWARE_PROXY_COUNT = env.int("AXES_IPWARE_PROXY_COUNT", default=2)
AXES_LOCKOUT_TEMPLATE = "axes/lockout.html"

# Wagtail 2FA settings
WAGTAIL_2FA_REQUIRED = env.bool("WAGTAIL_2FA_REQUIRED", default=False)


class AttrDict(dict):
    def __getattr__(self, item):
        return super().__getitem__(item)
    
    def __setattr__(self, item, value):
        globals()[item] = value
    
    def __setitem__(self, key, value):
        globals()[key] = value


for plugin in [*CLIMWEB_PLUGIN_NAMES]:
    try:
        mod = importlib.import_module(plugin + ".config.settings.settings")
        # The plugin should have a setup function which accepts a 'settings' object.
        # This settings object is an AttrDict shadowing our local variables so the
        # plugin can access the Django settings and modify them prior to startup.
        result = mod.setup(AttrDict(vars()))
    except ImportError as e:
        print("Could not import %s", plugin)
        print(e)

#  Logging
CLIMWEB_LOG_LEVEL = env.str("CLIMWEB_LOG_LEVEL", "INFO")
CLIMWEB_DATABASE_LOG_LEVEL = env.str("CLIMWEB_DATABASE_LOG_LEVEL", "ERROR")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "%(levelname)s %(asctime)s %(name)s.%(funcName)s:%(lineno)s- %("
                      "message)s "
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": CLIMWEB_DATABASE_LOG_LEVEL,
            "propagate": True,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": CLIMWEB_LOG_LEVEL,
    },
}

VUE_FRONTEND_USE_TYPESCRIPT = False
VUE_FRONTEND_USE_DEV_SERVER = DEBUG
VUE_FRONTEND_DEV_SERVER_URL = 'http://localhost:5173'
VUE_FRONTEND_DEV_SERVER_PATH = 'src'
VUE_FRONTEND_STATIC_PATH = 'vue'

WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY = env("WAGTAIL_NEWSLETTER_MAILCHIMP_API_KEY", default="")
WAGTAIL_NEWSLETTER_FROM_NAME = env("WAGTAIL_NEWSLETTER_FROM_NAME", default="")
WAGTAIL_NEWSLETTER_REPLY_TO = env("WAGTAIL_NEWSLETTER_REPLY_TO", default="")
