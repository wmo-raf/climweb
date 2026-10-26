"""
The reCAPTCHA tab of Settings -> Integration Settings.

How the keys are used is described in ``climweb.base.recaptcha``. Editors can
use the other tabs as before; the reCAPTCHA tab and its fields only exist for
superusers (``SUPERUSER_ONLY_PERMISSION`` drops them from everyone else's form,
so their saves can't change the keys). Changing the reCAPTCHA fields asks for a
fresh authenticator code, the secret key is write-only and encrypted at rest,
and saving with the keys switched on needs a ticked test checkbox drawn with
the entered site key, verified with the secret key; nothing is saved unless
Google accepts it.

Changes appear in the CMS history log like any other settings edit.
"""
from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, ObjectList, Panel

from climweb.base.recaptcha import (
    KeyCheckError,
    check_private_key,
    check_public_key,
    check_test_token,
    get_cms_keys,
)
from climweb.base.superuser_settings import SUPERUSER_ONLY_PERMISSION, ConfirmedSuperuserSettingsForm

RECAPTCHA_FIELDS = ("recaptcha_enabled", "recaptcha_public_key", "recaptcha_private_key")


class RecaptchaHelpPanel(Panel):
    """Read-only status and setup steps at the top of the tab."""

    class BoundPanel(Panel.BoundPanel):
        template_name = "admin/panels/recaptcha_settings_help_panel.html"

        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            context.update({
                "enabled": self.instance.recaptcha_enabled,
                "using_cms": get_cms_keys(getattr(self.instance, "site", None)) is not None,
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
                "key_name": self.form["recaptcha_public_key"].html_name,
                "token_name": self.form[IntegrationSettingsForm.TEST_TOKEN_FIELD].html_name,
                "token_errors": self.form.errors.get(IntegrationSettingsForm.TEST_TOKEN_FIELD),
                "recaptcha_domain": getattr(settings, "RECAPTCHA_DOMAIN", "www.google.com"),
            })
            return context


class IntegrationSettingsForm(ConfirmedSuperuserSettingsForm):
    TEST_TOKEN_FIELD = "recaptcha_test_token"

    guarded_fields = RECAPTCHA_FIELDS
    secret_fields = ("recaptcha_private_key",)
    secret_help_text = _(
        "Paste to set or change. Leave blank to keep the current secret key. "
        "It is never shown again after saving."
    )
    denied_message = _("Only superusers can change the reCAPTCHA settings.")
    confirmation_help_suffix = _("Only needed when you change the reCAPTCHA settings.")

    # Filled in by the test checkbox (see recaptcha_test_panel.html).
    recaptcha_test_token = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean(self):
        cleaned_data = super().clean()
        if not self.confirmed:
            return cleaned_data

        public_key = cleaned_data.get("recaptcha_public_key") or ""
        submitted_private_key = cleaned_data.get("recaptcha_private_key") or ""

        for name, value, check in (("recaptcha_public_key", public_key, check_public_key),
                                   ("recaptcha_private_key", submitted_private_key, check_private_key)):
            if value:
                try:
                    check(value)
                except KeyCheckError as e:
                    self.add_error(name, str(e))

        if not cleaned_data.get("recaptcha_enabled"):
            return cleaned_data

        # Everything below only matters when the keys will be used.
        if not public_key:
            self.add_error("recaptcha_public_key", _("Enter the site key."))
        private_key = self.get_secret("recaptcha_private_key")
        if not private_key:
            self.add_error("recaptcha_private_key", _("Enter the secret key."))
        elif private_key == public_key:
            self.add_error("recaptcha_private_key", _(
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


def recaptcha_tab():
    return ObjectList([
        RecaptchaHelpPanel(),
        MultiFieldPanel([
            FieldPanel("recaptcha_public_key", permission=SUPERUSER_ONLY_PERMISSION),
            FieldPanel("recaptcha_private_key", permission=SUPERUSER_ONLY_PERMISSION),
        ], heading=_("Keys")),
        RecaptchaTestPanel(heading=_("Test the keys")),
        FieldPanel("recaptcha_enabled", permission=SUPERUSER_ONLY_PERMISSION),
        FieldPanel("confirmation_code", permission=SUPERUSER_ONLY_PERMISSION),
    ], heading=_("reCAPTCHA"), permission=SUPERUSER_ONLY_PERMISSION)
