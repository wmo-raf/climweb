"""
reCAPTCHA keys, edited from Settings -> reCAPTCHA in the CMS.

How the keys are used is described in ``climweb.base.recaptcha``. The page is
guarded like the other server-secret settings (``climweb.base.superuser_settings``):
superusers only, every save asks for a fresh authenticator code, and the secret
key is write-only and encrypted at rest. Saving with the keys switched on needs
a ticked test checkbox drawn with the entered site key, verified with the
entered secret key; nothing is saved unless Google accepts it.

Changes appear in the CMS history log like any other settings edit.
"""
from django import forms
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, Panel
from wagtail.contrib.settings.models import BaseGenericSetting
from wagtail.contrib.settings.registry import register_setting

from climweb.base.backups.crypto import decrypt_text
from climweb.base.recaptcha import (
    KeyCheckError,
    RecaptchaKeys,
    check_private_key,
    check_public_key,
    check_test_token,
    get_cms_keys,
)
from climweb.base.superuser_settings import ConfirmedSuperuserSettingsForm, SuperuserOnlyPermissionPolicy

__all__ = ["RecaptchaSettings", "RecaptchaSettingsForm"]


class RecaptchaSettingsHelpPanel(Panel):
    """Read-only status and setup steps at the top of the page."""

    class BoundPanel(Panel.BoundPanel):
        template_name = "admin/panels/recaptcha_settings_help_panel.html"

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            context.update({
                "enabled": self.instance.enabled,
                "using_cms": get_cms_keys() is not None,
                "has_server_keys": bool(getattr(settings, "RECAPTCHA_PUBLIC_KEY", "")),
            })
            return context


class RecaptchaTestPanel(Panel):
    """The test checkbox, drawn with whatever is in the site key field."""

    class BoundPanel(Panel.BoundPanel):
        template_name = "admin/panels/recaptcha_test_panel.html"

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            context.update({
                "token_name": self.form[RecaptchaSettingsForm.TEST_TOKEN_FIELD].html_name,
                "token_errors": self.form.errors.get(RecaptchaSettingsForm.TEST_TOKEN_FIELD),
                "recaptcha_domain": getattr(settings, "RECAPTCHA_DOMAIN", "www.google.com"),
            })
            return context


class RecaptchaSettingsForm(ConfirmedSuperuserSettingsForm):
    TEST_TOKEN_FIELD = "test_token"

    secret_fields = ("private_key",)
    secret_help_text = _(
        "Paste to set or change. Leave blank to keep the current secret key. "
        "It is never shown again after saving."
    )
    denied_message = _("Only superusers can change the reCAPTCHA settings.")

    # Filled in by the test checkbox (see recaptcha_test_panel.html).
    test_token = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean(self):
        cleaned_data = super().clean()
        if not self.confirmed:
            return cleaned_data

        public_key = cleaned_data.get("public_key") or ""
        submitted_private_key = cleaned_data.get("private_key") or ""

        for name, value, check in (("public_key", public_key, check_public_key),
                                   ("private_key", submitted_private_key, check_private_key)):
            if value:
                try:
                    check(value)
                except KeyCheckError as e:
                    self.add_error(name, str(e))

        if not cleaned_data.get("enabled"):
            return cleaned_data

        # Everything below only matters when the keys will be used.
        if not public_key:
            self.add_error("public_key", _("Enter the site key."))
        private_key = self.get_secret("private_key")
        if not private_key:
            self.add_error("private_key", _("Enter the secret key."))
        elif private_key == public_key:
            self.add_error("private_key", _(
                "The secret key is the same as the site key. Copy the secret key "
                "from the reCAPTCHA admin console."
            ))
        if self.errors:
            return cleaned_data

        try:
            check_test_token(cleaned_data.get(self.TEST_TOKEN_FIELD), private_key)
        except KeyCheckError as e:
            self.add_error(self.TEST_TOKEN_FIELD, str(e))

        return cleaned_data


@register_setting(icon="lock")
class RecaptchaSettings(BaseGenericSetting):
    base_form_class = RecaptchaSettingsForm

    enabled = models.BooleanField(
        default=False,
        verbose_name=_("Use these keys on the website's forms"),
        help_text=_(
            "When off, the forms use the reCAPTCHA keys from the server "
            "configuration, as before. While on, every save checks the keys "
            "with the test box above; nothing is saved if Google rejects them."
        ),
    )
    public_key = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Site key"),
        help_text=_("Shown in the page to visitors, so it is not secret."),
    )
    # Stored ENCRYPTED at rest; edited via the write-only form field.
    private_key = models.CharField(max_length=512, blank=True, verbose_name=_("Secret key"))

    class Meta:
        verbose_name = _("reCAPTCHA")

    @classmethod
    def get_permission_policy(cls):
        # Hides the menu item and refuses the page to everyone else, even if
        # the permission is ticked for a group in Settings -> Groups.
        return SuperuserOnlyPermissionPolicy(cls)

    def get_private_key(self):
        return decrypt_text(self.private_key) if self.private_key else ""

    def get_keys(self):
        """Raises if the stored secret key can't be decrypted (e.g. SECRET_KEY
        was changed)."""
        return RecaptchaKeys(public_key=self.public_key, private_key=self.get_private_key())

    panels = [
        RecaptchaSettingsHelpPanel(),
        MultiFieldPanel([
            FieldPanel("public_key"),
            FieldPanel("private_key"),
        ], heading=_("Keys")),
        RecaptchaTestPanel(heading=_("Test the keys")),
        FieldPanel("enabled"),
        FieldPanel("confirmation_code"),
    ]
