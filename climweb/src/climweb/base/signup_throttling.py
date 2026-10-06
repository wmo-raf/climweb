"""Rate limits for geomanager's public account endpoints.

geomanager lets anyone register a map-viewer account (`api/auth/register/`) or
ask for a password-reset email (`api/auth/reset-password/`). Both send email to
whatever address is submitted, and every new account also emails the site's
superusers (see user_notifications.py), so unthrottled they let a bot create
accounts in bulk and flood inboxes.

Each endpoint gets two limits:

* per client IP, which stops a single bot, and
* site-wide, which caps the total when a bot spreads across many IPs.

The views are geomanager's own, re-mounted with throttling in config/urls.py
ahead of geomanager's URLs. Rates come from `PUBLIC_ACCOUNT_RATE_LIMITS`.
"""

from django.conf import settings
from geomanager.views.auth import RegisterView, ResetPasswordView
from rest_framework.throttling import SimpleRateThrottle


class _SettingsRateThrottle(SimpleRateThrottle):
    def get_rate(self):
        # Read at request time rather than DRF's import-time THROTTLE_RATES, so
        # the rates follow settings (and override_settings in tests).
        return settings.PUBLIC_ACCOUNT_RATE_LIMITS[self.scope]


def client_ip(request):
    """The client address as seen by the outermost of our own proxies.

    Each proxy appends the address it received the request from to
    X-Forwarded-For (nginx's `$proxy_add_x_forwarded_for`), so with N proxies in
    front of Django the client is the Nth entry from the right. Anything to the
    left of that was supplied by the client and could be forged, so it is never
    used. N comes from AXES_IPWARE_PROXY_COUNT, which describes the same
    deployment.
    """
    proxy_count = getattr(settings, "AXES_IPWARE_PROXY_COUNT", 0) or 0
    forwarded = [
        address.strip()
        for address in request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")
        if address.strip()
    ]
    if proxy_count and forwarded:
        # Fewer entries than proxies means the request skipped a proxy we
        # expected; the leftmost entry is then the best we have.
        return forwarded[-min(proxy_count, len(forwarded))]
    return request.META.get("REMOTE_ADDR", "")


class _PerIPThrottle(_SettingsRateThrottle):
    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": client_ip(request)}


class _SiteWideThrottle(_SettingsRateThrottle):
    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": "all"}


class RegisterPerIPThrottle(_PerIPThrottle):
    scope = "register_per_ip"


class RegisterSiteWideThrottle(_SiteWideThrottle):
    scope = "register_site_wide"


class PasswordResetPerIPThrottle(_PerIPThrottle):
    scope = "password_reset_per_ip"


class PasswordResetSiteWideThrottle(_SiteWideThrottle):
    scope = "password_reset_site_wide"


class ThrottledRegisterView(RegisterView):
    throttle_classes = [RegisterPerIPThrottle, RegisterSiteWideThrottle]


class ThrottledResetPasswordView(ResetPasswordView):
    throttle_classes = [PasswordResetPerIPThrottle, PasswordResetSiteWideThrottle]
