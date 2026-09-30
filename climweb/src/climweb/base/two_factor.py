"""Email fallback for two-factor authentication.

Editors who lose or replace the phone holding their authenticator app would
otherwise be locked out until an administrator removes their device. Instead,
the verification page offers to email them a one-time code. Once signed in with
it they can register their new phone from "Manage your 2FA devices".

The code is delivered through django-otp's `EmailDevice`. django-otp accepts a
token from any *confirmed* device, so a confirmed `EmailDevice` makes the stock
wagtail-2fa verification form accept the emailed code with no further changes.

Having a confirmed device of any kind is also what tells the 2FA middleware that
a user is enrolled. To keep "an administrator removes your authenticator, then
you enrol again with just your password" working, the email device therefore
only exists alongside an authenticator: it is created on demand for users who
have one, and deleted as soon as their last one is removed.
"""

import logging

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy
from django.views.decorators.http import require_POST
from wagtail.admin.views.account import BaseSettingsPanel
from django_otp.plugins.otp_email.models import EmailDevice
from django_otp.plugins.otp_totp.models import TOTPDevice

logger = logging.getLogger(__name__)

EMAIL_DEVICE_NAME = "Email"


def has_authenticator(user):
    return TOTPDevice.objects.devices_for_user(user, confirmed=True).exists()


def mask_email(address):
    """`jane.doe@met.go.ke` -> `j*******@met.go.ke`, enough to recognise it."""
    local, _sep, domain = address.partition("@")
    if not domain:
        return address
    return f"{local[:1]}{'*' * max(len(local) - 1, 1)}@{domain}"


def _back_to_verification(next_url):
    url = reverse("wagtail_2fa_auth")
    if next_url:
        # wagtail-2fa's LoginView validates `next` before redirecting to it.
        url = f"{url}?{urlencode({'next': next_url})}"
    return redirect(url)


@require_POST
def send_email_code(request):
    user = request.user
    next_url = request.POST.get("next", "")

    if not user.is_authenticated:
        return redirect_to_login(reverse("wagtail_2fa_auth"))

    if user.is_verified():
        return _back_to_verification(next_url)

    # Users without an authenticator are enrolling, not recovering; they don't
    # need a code. Refusing here also keeps us from creating an EmailDevice that
    # would count as "enrolled" for someone who never set 2FA up.
    if not has_authenticator(user):
        return redirect("wagtail_2fa_device_new")

    if not user.email:
        messages.error(
            request,
            _(
                "There is no email address on your account, so we can't send you "
                "a code. Please ask a site administrator to reset your "
                "two-factor authentication."
            ),
        )
        return _back_to_verification(next_url)

    device, _created = EmailDevice.objects.get_or_create(
        user=user, defaults={"name": EMAIL_DEVICE_NAME, "confirmed": True}
    )

    allowed, _info = device.generate_is_allowed()
    if not allowed:
        messages.warning(
            request,
            _(
                "A code was sent to %(email)s less than a minute ago. Please check "
                "your inbox (and spam folder) or wait a moment before asking for "
                "another."
            )
            % {"email": mask_email(user.email)},
        )
        return _back_to_verification(next_url)

    try:
        device.generate_challenge(
            extra_context={
                "user": user,
                "site_name": settings.WAGTAIL_SITE_NAME,
                "minutes": settings.OTP_EMAIL_TOKEN_VALIDITY // 60,
            }
        )
    except Exception:
        logger.exception("Could not send 2FA email code to user %s", user.pk)
        messages.error(
            request,
            _(
                "We couldn't send the email. The site's email settings may not be "
                "configured. Please ask a site administrator to reset your "
                "two-factor authentication."
            ),
        )
        return _back_to_verification(next_url)

    messages.success(
        request,
        _(
            "We've emailed a 6-digit code to %(email)s. Enter it below. It "
            "expires in %(minutes)d minutes. You'll then be taken to your 2FA "
            "devices page to set up your new phone."
        )
        % {
            "email": mask_email(user.email),
            "minutes": settings.OTP_EMAIL_TOKEN_VALIDITY // 60,
        },
    )
    # Someone using the email fallback has lost their authenticator, so the
    # next thing they need is the page for registering a new one.
    return _back_to_verification(
        reverse("wagtail_2fa_device_list", kwargs={"user_id": user.pk})
    )


class TwoFactorSettingsPanel(BaseSettingsPanel):
    """Link to the 2FA devices page from the main Account page.

    wagtail-2fa only adds its link under Account -> "More actions", which is
    easy to miss.
    """

    name = "two_factor"
    title = _lazy("Two-factor authentication")
    order = 550  # just after "Password"
    template_name = "two_factor/account_panel.html"

    def get_form(self):
        # Nothing to edit here, but the Account view collects media from and
        # validates every panel's form, so hand it an empty, unbound one.
        return forms.Form()

    def get_context_data(self):
        return {
            "devices_url": reverse(
                "wagtail_2fa_device_list", kwargs={"user_id": self.user.pk}
            ),
            "has_authenticator": has_authenticator(self.user),
        }


@receiver(post_delete, sender=TOTPDevice)
def remove_email_fallback_with_last_authenticator(sender, instance, **kwargs):
    """Without an authenticator, an email device alone must not keep someone
    "enrolled" — that would stop them re-enrolling after an admin reset."""
    if not TOTPDevice.objects.filter(user_id=instance.user_id, confirmed=True).exists():
        EmailDevice.objects.filter(user_id=instance.user_id).delete()
