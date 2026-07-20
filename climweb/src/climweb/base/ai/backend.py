"""
A Wagtail AI "LLM" backend that pulls its provider, model and API key from the
CMS admin (``AISettings``) at request time, instead of from Django settings /
environment variables.

Why: ClimWeb ships one deployment per NMHS. Requiring each of them to set an
``OPENAI_API_KEY`` env var (and redeploy) to switch the assistant on doesn't
scale. Instead, ``settings.WAGTAIL_AI`` points at this backend, and the actual
credentials live — encrypted — in the database, editable from Settings -> AI
Assistant. See ``climweb.base.models.ai_settings``.

The stock ``LLMBackend`` resolves its model + init kwargs once, from settings.
We override ``get_llm_model`` so the model ID and API key are read fresh on
every call, from the current site's ``AISettings``.
"""
import llm
from django.core.exceptions import ImproperlyConfigured
from wagtail_ai.ai.llm import LLMBackend


def get_ai_settings():
    """Return the AISettings for the default site, or None.

    ClimWeb deployments are effectively single-site, so we resolve against the
    default site rather than the request (the backend has no request context).
    """
    # Imported lazily so this module is importable before apps are ready.
    from wagtail.models import Site

    from climweb.base.models.ai_settings import AISettings

    site = Site.objects.filter(is_default_site=True).first() or Site.objects.first()
    if site is None:
        return None
    return AISettings.for_site(site)


class CMSConfiguredLLMBackend(LLMBackend):
    """LLM backend whose model and API key come from the CMS, not settings."""

    def get_llm_model(self) -> "llm.Model":
        ai_settings = get_ai_settings()
        if ai_settings is None or not ai_settings.is_configured():
            raise ImproperlyConfigured(
                "The AI assistant is not configured. Set it up in the CMS under "
                "Settings -> AI Assistant (enable it, choose a provider and enter "
                "an API key)."
            )

        model = llm.get_model(ai_settings.resolved_model_id())

        api_key = ai_settings.get_api_key()
        if api_key:
            # The "LLM" library reads the credential from the model's ``key``
            # attribute (falling back to provider env vars otherwise).
            model.key = api_key

        # Preserve any static init kwargs configured in settings.WAGTAIL_AI.
        if self.config.init_kwargs is not None:
            for config_key, config_val in self.config.init_kwargs.items():
                setattr(model, config_key, config_val)

        return model
