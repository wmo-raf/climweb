"""
DORMANT: AI assistant settings.

The optional Wagtail AI writing assistant has been removed from ClimWeb (the
``wagtail-ai`` / ``llm-anthropic`` dependencies pulled in ``any-llm-sdk``, which
is not installable in the build image). This model is deliberately kept — and
still registered with Django — so that migrations 0048/0049 and the merge
migrations that depend on them stay valid, and so that existing per-site rows
are not dropped from deployed databases.

It is NOT registered with ``@register_setting``, so it does not appear anywhere
in the CMS admin. If the assistant is reinstated, re-add the decorator (and the
``climweb.base.ai`` package + settings wiring) rather than recreating the model.
"""
from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _

from django.conf import settings

from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, ObjectList, TabbedInterface
from wagtail.contrib.settings.models import BaseSiteSetting

from climweb.base.backups.crypto import decrypt_text, encrypt_text


def register_ai_setting(cls):
    """Register the AI Assistant settings panel only when AI is enabled.

    Unlike wagtail_ai's own menus (Prompts, Agents) which come/go with the
    package, this panel is climweb's own and would otherwise show even after
    wagtail_ai is removed. Gating it on WAGTAIL_AI_ENABLED keeps the whole AI
    surface behind the single CLIMWEB_AI_ENABLED switch.
    """
    if getattr(settings, "WAGTAIL_AI_ENABLED", False):
        return register_setting(icon="wand")(cls)
    return cls


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
