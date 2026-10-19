"""
Shared pieces for CMS settings pages that hold server secrets.

Settings that used to live only in the server's ``.env`` (reCAPTCHA keys, SMTP
credentials, ...) can be edited in the CMS, but more tightly guarded than other
settings:

  * superusers only (``SuperuserOnlyPermissionPolicy``), whatever the group
    permissions say,
  * every save asks for a fresh authenticator code, or the account password
    for a superuser without an authenticator (``ConfirmedSuperuserSettingsForm``),
  * secrets are write-only in the form and encrypted at rest with
    ``climweb.base.backups.crypto``.
"""
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.permission_policies.base import BasePermissionPolicy

from climweb.base.backups.crypto import decrypt_text, encrypt_text


class SuperuserOnlyPermissionPolicy(BasePermissionPolicy):
    def user_has_permission(self, user, action):
        return user.is_active and user.is_superuser

    def user_has_any_permission(self, user, actions):
        return user.is_active and user.is_superuser

    def users_with_any_permission(self, actions):
        return get_user_model().objects.filter(is_active=True, is_superuser=True)

    def users_with_permission(self, action):
        return self.users_with_any_permission([action])


def user_has_authenticator(user):
    from django_otp.plugins.otp_totp.models import TOTPDevice

    return TOTPDevice.objects.devices_for_user(user, confirmed=True).exists()


def verify_user_code(user, code):
    """True if ``code`` is a current authenticator code for ``user`` or, for a
    user with no authenticator, their account password."""
    from django_otp.plugins.otp_totp.models import TOTPDevice

    code = (code or "").strip()
    if not code:
        return False
    devices = list(TOTPDevice.objects.devices_for_user(user, confirmed=True))
    if devices:
        token = code.replace(" ", "")
        # verify_token() applies django-otp's throttling after failed attempts.
        return any(device.verify_token(token) for device in devices)
    return user.check_password(code)


class ConfirmedSuperuserSettingsForm(WagtailAdminModelForm):
    """Settings form that only a superuser can save, after confirming it's them.

    Fields named in ``secret_fields`` are write-only: never rendered back,
    blank keeps the stored value, and a new value is stored encrypted.
    Subclasses call ``super().clean()`` and should stop validating when
    ``self.confirmed`` is False.
    """

    secret_fields = ()
    secret_help_text = _("Paste to set or change. Leave blank to keep the current value.")
    denied_message = _("Only superusers can change these settings.")

    confirmation_code = forms.CharField(
        required=True,
        label=_("Confirm it's you"),
        widget=forms.PasswordInput(render_value=False, attrs={"autocomplete": "one-time-code"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.confirmed = False
        # Snapshot the stored (encrypted) secrets before the ModelForm can
        # overwrite them with the blank input values on save.
        self._stored_secrets = {name: getattr(self.instance, name, "") for name in self.secret_fields}

        for name in self.secret_fields:
            if name in self.fields:
                f = self.fields[name]
                f.required = False
                f.initial = ""
                f.widget = forms.PasswordInput(render_value=False, attrs={"autocomplete": "new-password"})
                f.help_text = self.secret_help_text

        user = getattr(self, "for_user", None)
        if user is not None and not user_has_authenticator(user):
            self.fields["confirmation_code"].help_text = _(
                "Enter your account password to confirm this change."
            )
        else:
            self.fields["confirmation_code"].help_text = _(
                "Enter the current 6-digit code from your authenticator app to "
                "confirm this change."
            )

    def clean(self):
        cleaned_data = super().clean()
        user = getattr(self, "for_user", None)

        if user is None or not user.is_active or not user.is_superuser:
            raise ValidationError(self.denied_message)

        if not verify_user_code(user, cleaned_data.get("confirmation_code")):
            self.add_error(
                "confirmation_code",
                _("That code (or password) is not correct. Please try again."),
            )
            return cleaned_data

        self.confirmed = True
        return cleaned_data

    def get_secret(self, name):
        """The submitted value of a secret field or, if left blank, the stored
        one decrypted ("" if it can't be decrypted, e.g. SECRET_KEY changed)."""
        submitted = self.cleaned_data.get(name) or ""
        if submitted:
            return submitted
        stored = self._stored_secrets.get(name)
        try:
            return decrypt_text(stored) if stored else ""
        except Exception:
            return ""

    def save(self, commit=True):
        instance = super().save(commit=False)

        for name in self.secret_fields:
            submitted = self.cleaned_data.get(name) or ""
            if submitted:
                setattr(instance, name, encrypt_text(submitted))
            else:
                setattr(instance, name, self._stored_secrets[name])

        if commit:
            instance.save()
        return instance
