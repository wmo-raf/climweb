"""
Wagtail AI configuration, managed entirely from the CMS admin.

ClimWeb runs one deployment per NMHS, and most do not have the capacity (or the
budget) to manage an AI provider key from the server / docker-compose. So the
provider and API key are configured here, in Settings -> AI Assistant, instead
of the environment — no server access, no per-country redeploy.

The API key is stored ENCRYPTED at rest (same Fernet helper used for the backup
OAuth secret, keyed off ``SECRET_KEY``) and is write-only in the form: it is
never rendered back into the page after being saved.

The values entered here are consumed at request time by the custom Wagtail AI
backend in ``climweb.base.ai.backend`` — see that module for how the key and
model are injected into the "LLM" library.
"""
from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _

from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, ObjectList, TabbedInterface
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.contrib.settings.registry import register_setting

from climweb.base.backups.crypto import decrypt_text, encrypt_text


class AIProvider(models.TextChoices):
    OPENAI = "openai", _("OpenAI")
    ANTHROPIC = "anthropic", _("Anthropic (Claude)")


# Default model per provider, used when no explicit model override is entered.
# Model IDs must be recognisable by the "LLM" library (run ``llm models`` to
# list what is installed). The Anthropic models require the ``llm-anthropic``
# plugin to be installed in the image.
PROVIDER_DEFAULT_MODEL = {
    AIProvider.OPENAI: "gpt-4o-mini",
    # Anthropic retires older model aliases (e.g. claude-3-5-haiku-latest now
    # 404s), so keep this pointed at a current model. Override per-site via the
    # Model field if needed; run ``llm models`` to see what's available.
    AIProvider.ANTHROPIC: "claude-haiku-4.5",
}


class AISettingsForm(WagtailAdminModelForm):
    """Makes the API key write-only: it is never rendered back into the form,
    and is encrypted on save. Leaving it blank keeps the stored key."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Snapshot the stored (encrypted) key before the ModelForm can overwrite
        # it with the blank input value on save.
        self._stored_api_key = getattr(self.instance, "api_key", "")

        if "api_key" in self.fields:
            f = self.fields["api_key"]
            f.required = False
            f.initial = ""
            f.widget = forms.PasswordInput(render_value=False)
            f.help_text = _("Paste to set or change. Leave blank to keep the current key.")

    def save(self, commit=True):
        instance = super().save(commit=False)

        submitted_key = self.cleaned_data.get("api_key", "")
        if submitted_key:
            instance.api_key = encrypt_text(submitted_key)
        else:
            instance.api_key = self._stored_api_key

        if commit:
            instance.save()
        return instance


@register_setting(icon="wand")
class AISettings(BaseSiteSetting):
    base_form_class = AISettingsForm

    enabled = models.BooleanField(
        default=False,
        verbose_name=_("Enable AI assistant"),
        help_text=_(
            "When enabled, AI writing tools appear in the rich text editor. "
            "You must select a provider and enter an API key below first."
        ),
    )

    provider = models.CharField(
        max_length=20,
        choices=AIProvider.choices,
        default=AIProvider.OPENAI,
        verbose_name=_("Provider"),
        help_text=_("The AI service to use. Choose the one you have an API key for."),
    )

    model_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Model (optional)"),
        help_text=_(
            "Leave blank to use a sensible default for the selected provider "
            "(OpenAI: gpt-4o-mini, Claude: claude-haiku-4.5). Only set this if "
            "you want a specific model. Provider model names change over time; if "
            "you get a 'model not found' error, enter a current one here."
        ),
    )

    # Stored ENCRYPTED at rest; edited via the write-only form field above.
    api_key = models.CharField(
        max_length=512,
        blank=True,
        verbose_name=_("API key"),
    )

    class Meta:
        verbose_name = _("AI Assistant")

    # ------------------------------------------------------------------ #
    # Credential / config helpers.
    # ------------------------------------------------------------------ #
    def get_api_key(self):
        if not self.api_key:
            return ""
        try:
            return decrypt_text(self.api_key)
        except Exception:
            return ""

    def resolved_model_id(self):
        if self.model_id:
            return self.model_id
        return PROVIDER_DEFAULT_MODEL.get(self.provider, PROVIDER_DEFAULT_MODEL[AIProvider.OPENAI])

    def is_configured(self):
        """True when the assistant is switched on and has a usable key."""
        return bool(self.enabled and self.get_api_key())

    edit_handler = TabbedInterface([
        ObjectList([
            MultiFieldPanel([
                FieldPanel("enabled"),
                FieldPanel("provider"),
                FieldPanel("model_id"),
                FieldPanel("api_key"),
            ], heading=_("AI provider")),
        ], heading=_("AI Assistant")),
    ])
