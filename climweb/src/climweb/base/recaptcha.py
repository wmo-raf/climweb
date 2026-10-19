"""
reCAPTCHA keys configured from the CMS.

Settings -> Integration Settings -> reCAPTCHA (a tab only superusers see) lets
a superuser enter the site and secret keys in the browser, so a country no
longer needs server access (or a docker-compose change) to set up or replace
them. The secret key is stored encrypted with the same key as the backup
credentials (see ``backups/crypto.py``).

django-recaptcha reads ``RECAPTCHA_PUBLIC_KEY`` / ``RECAPTCHA_PRIVATE_KEY``
from Django settings when a ``ReCaptchaField`` is created, and wagtailcaptcha
creates one each time a form page builds its form. ``SiteCaptchaFormBuilder``
swaps that field for ``SiteReCaptchaField``, which is created with the keys
from ``get_active_keys()`` for the form page's site instead:

  * CMS keys switched on  -> the keys saved in the CMS,
  * otherwise             -> the RECAPTCHA_* environment variables, as before.

Every form page with a captcha must inherit ``SiteCaptchaFormMixin`` (which
uses ``SiteCaptchaFormBuilder`` unless the page sets a subclass of it, such as
``climweb.base.forms.CustomWagtailCaptchaFormBuilder``).
"""
import re
from dataclasses import dataclass
from urllib.error import URLError

from django.conf import settings
from django.db import DatabaseError
from django.utils.translation import gettext as _
from django_recaptcha import client
from django_recaptcha.constants import TEST_PRIVATE_KEY, TEST_PUBLIC_KEY
from django_recaptcha.fields import ReCaptchaField
from loguru import logger
from wagtailcaptcha.forms import WagtailCaptchaFormBuilder

# Google's keys are 40 URL-safe characters (they normally start with "6L").
KEY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{40}$")


@dataclass(frozen=True)
class RecaptchaKeys:
    public_key: str
    private_key: str


def get_server_keys():
    return RecaptchaKeys(
        public_key=getattr(settings, "RECAPTCHA_PUBLIC_KEY", ""),
        private_key=getattr(settings, "RECAPTCHA_PRIVATE_KEY", ""),
    )


def get_cms_keys(site=None):
    """The keys saved in the CMS for ``site`` (default: the default site), or
    None to use the environment variables.

    Never raises: a missing table or column (before migrating), an
    undecryptable secret key (SECRET_KEY rotated) or missing keys all fall back
    to the environment so that the forms keep working.
    """
    from wagtail.models import Site

    from climweb.base.models import IntegrationSettings

    try:
        site = site or Site.objects.filter(is_default_site=True).first()
        if site is None:
            return None
        integration_settings = IntegrationSettings.for_site(site)
    except DatabaseError:
        return None

    if not integration_settings.recaptcha_enabled:
        return None

    try:
        keys = integration_settings.get_recaptcha_keys()
    except Exception as e:
        logger.warning(f"[RECAPTCHA] CMS reCAPTCHA keys unusable, using server settings instead: {e!r}")
        return None
    if not keys.public_key or not keys.private_key:
        logger.warning("[RECAPTCHA] CMS reCAPTCHA keys incomplete, using server settings instead")
        return None
    return keys


def get_active_keys(site=None):
    return get_cms_keys(site) or get_server_keys()


class SiteReCaptchaField(ReCaptchaField):
    """``ReCaptchaField`` using the keys from ``get_active_keys()``."""

    def __init__(self, public_key=None, private_key=None, *args, site=None, **kwargs):
        if not public_key and not private_key:
            keys = get_active_keys(site)
            public_key, private_key = keys.public_key, keys.private_key
        super().__init__(public_key, private_key, *args, **kwargs)


class SiteCaptchaFormBuilder(WagtailCaptchaFormBuilder):
    # Set by SiteCaptchaFormMixin; None means the default site.
    site = None

    @property
    def formfields(self):
        fields = super().formfields
        fields[self.CAPTCHA_FIELD_NAME] = SiteReCaptchaField(label="", site=self.site)
        return fields


class SiteCaptchaFormMixin:
    """For form pages with a captcha: builds the form with the reCAPTCHA keys
    of the page's own site. List it before ``WagtailCaptchaEmailForm``."""

    form_builder = SiteCaptchaFormBuilder

    def get_form_class(self):
        builder = self.form_builder(self.get_form_fields())
        builder.site = self.get_site()
        return builder.get_form_class()


class KeyCheckError(Exception):
    """A key was rejected; the message is meant for the site administrator."""


def check_public_key(public_key):
    if public_key == TEST_PUBLIC_KEY:
        raise KeyCheckError(_(
            "This is Google's public test key, which lets every submission "
            "through. Create keys for your site instead."
        ))
    if not KEY_PATTERN.match(public_key):
        raise KeyCheckError(_(
            "This doesn't look like a reCAPTCHA key. Copy the whole site key "
            "(40 characters) from the reCAPTCHA admin console."
        ))


def check_private_key(private_key):
    if private_key == TEST_PRIVATE_KEY:
        raise KeyCheckError(_(
            "This is Google's secret test key, which lets every submission "
            "through. Create keys for your site instead."
        ))
    if not KEY_PATTERN.match(private_key):
        raise KeyCheckError(_(
            "This doesn't look like a reCAPTCHA key. Copy the whole secret key "
            "(40 characters) from the reCAPTCHA admin console."
        ))


def check_test_token(token, private_key):
    """Verify, with Google, a token from the test checkbox on the settings page.

    Google only looks at the secret key once it has a real token, so this is
    the only reliable test: it passes only if the site key that drew the
    checkbox and the secret key belong together, the key type is the
    "I'm not a robot" checkbox and this website's domain is allowed.
    """
    if not token:
        raise KeyCheckError(_(
            "Tick the \"I'm not a robot\" test box below so the keys can be "
            "checked before they are used."
        ))
    try:
        response = client.submit(recaptcha_response=token, private_key=private_key, remoteip="")
    except (URLError, OSError, ValueError) as e:
        raise KeyCheckError(_(
            "Could not reach Google to check the keys, so nothing was saved. "
            "The server must be able to reach %(domain)s for reCAPTCHA to work "
            "at all. (Details: %(detail)s)"
        ) % {
            "domain": getattr(settings, "RECAPTCHA_DOMAIN", "www.google.com"),
            "detail": str(e) or e.__class__.__name__,
        })

    if response.is_valid:
        return
    codes = set(response.error_codes)
    if "invalid-input-secret" in codes:
        message = _(
            "Google did not accept the secret key. Check that you copied the "
            "secret key (not the site key) completely."
        )
    elif "timeout-or-duplicate" in codes:
        message = _("The test box expired. Tick it again and save.")
    elif "invalid-input-response" in codes:
        message = _(
            "The site key and secret key don't belong together. Copy both "
            "from the same site in the reCAPTCHA admin console."
        )
    else:
        message = _("Google did not accept the keys.")
    raise KeyCheckError(_("%(message)s (Details: %(detail)s)") % {
        "message": message,
        "detail": ", ".join(response.error_codes) or "-",
    })
