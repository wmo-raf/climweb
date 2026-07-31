"""Two-factor authentication middleware.

wagtail-2fa is driven entirely by the `WAGTAIL_2FA_REQUIRED` setting, and every
deployment built from `.env.sample` shipped with `WAGTAIL_2FA_REQUIRED=False`
baked into its `.env`. An explicit value always beats a settings default, so
changing the default cannot reach those instances — they would each need someone
with shell access to edit `.env`.

Superuser accounts are the ones worth protecting: they can read server logs,
manage every user, and reach the Django admin. This middleware therefore requires
2FA of superusers on admin URLs, whatever `WAGTAIL_2FA_REQUIRED` happens to say,
and defers to wagtail-2fa's own permission-based logic for everyone else.

The rule is scoped to the Wagtail and Django admin paths on purpose. Upstream
applies its check to every URL, so an un-enrolled user cannot load the public
site while logged in — which is a confusing way to discover you need to set up
2FA. Here the public site stays readable and the challenge appears when you try
to reach the admin.

`CLIMWEB_2FA_SUPERUSER_REQUIRED=False` remains as an escape hatch for a site that
gets stuck (for example a lone superuser who cannot enrol a device), since the
alternative would be an unrecoverable lockout on an instance nobody can SSH into.
"""

import logging

import django_otp
from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.urls import Resolver404, resolve, reverse
from wagtail_2fa.middleware import VerifyUserPermissionsMiddleware

logger = logging.getLogger(__name__)


class SuperuserVerifyUserMiddleware(VerifyUserPermissionsMiddleware):
    """Force 2FA for superusers; behave exactly like wagtail-2fa otherwise."""

    def _admin_paths(self):
        """URL prefixes the superuser rule applies to.

        Both admins matter: the Wagtail admin exposes the server logs, and the
        Django admin can edit users and delete other people's 2FA devices.
        """
        paths = []
        for setting_name in ("ADMIN_URL_PATH", "DJANGO_ADMIN_URL_PATH"):
            value = (getattr(settings, setting_name, "") or "").strip("/")
            if value:
                paths.append(f"/{value}/")
        return paths

    def _is_admin_request(self, request):
        # path_info rather than path, so a deployment using FORCE_SCRIPT_NAME
        # still matches (path would carry the script prefix).
        path = request.path_info
        return any(path.startswith(prefix) for prefix in self._admin_paths())

    def _superuser_forced(self, request):
        if not getattr(settings, "CLIMWEB_2FA_SUPERUSER_REQUIRED", True):
            return False

        # Scoped to the admin: an un-enrolled superuser should still be able to
        # browse their own public site while logged in. Upstream wagtail-2fa
        # applies its rule site-wide, which locks them out of the homepage too.
        if not self._is_admin_request(request):
            return False

        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and user.is_superuser)

    def _url_name(self, request):
        try:
            return resolve(request.path_info).url_name
        except Resolver404:
            # An unmatched URL is on its way to a 404. Upstream doesn't guard
            # this because it only resolves once it already knows the request is
            # for an admin user; we run earlier and more broadly, so a stray URL
            # must not turn into a 500.
            return None

    def _require_verified_user(self, request):
        if not self._superuser_forced(request):
            return super()._require_verified_user(request)

        # Mirror upstream's exemptions, or the redirects below would loop on the
        # login and enrolment pages themselves.
        url_name = self._url_name(request)
        if url_name in self._allowed_url_names:
            return False
        if url_name in self._allowed_url_names_no_device:
            if not django_otp.user_has_device(request.user, confirmed=True):
                return False

        return True

    def process_request(self, request):
        response = super().process_request(request)
        if response is not None:
            return response

        # Upstream only sends a user to enrolment when WAGTAIL_2FA_REQUIRED is
        # set, so with the flag off a superuser without a device sails straight
        # through. Handle that case ourselves.
        if not self._superuser_forced(request):
            return None
        if not self._require_verified_user(request):
            return None
        if django_otp.user_has_device(request.user, confirmed=True):
            # Already enrolled: the parent has issued the verification redirect.
            return None

        return redirect_to_login(
            request.get_full_path(), login_url=reverse("wagtail_2fa_device_new")
        )
