"""
Make wagtail-ai's *agent* features use the per-site CMS key.

Wagtail AI has two separate pipelines:

  * the rich-text editor "magic wand" uses the BACKENDS path (the `llm` library)
    which we already point at the CMS key via ``CMSConfiguredLLMBackend``;
  * everything else — content feedback, image title/description, contextual
    alt text, related-page suggestions and the title/description field panels —
    uses the AGENT path (``django_ai_core`` + the ``any_llm`` library). Those
    read their provider + key from ``settings.WAGTAIL_AI["PROVIDERS"]`` (or the
    ``OPENAI_API_KEY`` env var), NOT from our encrypted ``AISettings``.

All of the agent features funnel through a single function,
``wagtail_ai.agents.base.get_provider(alias)``, which returns a dict of kwargs
(``provider``, ``model``, ``api_key`` …) used to build the LLM client. We
monkeypatch it so, when the CMS assistant is configured, it returns the site's
provider, model and *decrypted* key. One override unlocks every agent feature on
the per-site key — no environment variables, consistent with the editor wand.

Caveat: the agent path uses ``any_llm``, whose model-id namespace differs from
the ``llm`` library's. ``any_llm`` talks to the provider API directly, so an
Anthropic model needs its API id (``claude-haiku-4-5``) rather than the ``llm``
alias (``claude-haiku-4.5``). ``_agent_model_id`` maps the CMS value across.
"""
import logging

logger = logging.getLogger(__name__)

# Model used by the agent path when the CMS "Model" field is left blank.
# These are ids understood by the `any_llm` library / the provider APIs. They
# must be vision-capable so image alt-text works too.
AGENT_DEFAULT_MODEL = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5",
}

# Keeps a reference to wagtail-ai's original get_provider for the fallback path.
_original_get_provider = None


def _agent_model_id(ai_settings):
    """Translate the CMS model id into one the `any_llm` agent path understands."""
    model = (ai_settings.model_id or "").strip()
    if not model:
        return AGENT_DEFAULT_MODEL.get(ai_settings.provider, AGENT_DEFAULT_MODEL["openai"])
    # Drop any "anthropic/" / "openai/" prefix from an llm-library style id.
    model = model.split("/")[-1]
    # llm's Anthropic aliases use dots ("claude-haiku-4.5"); the Anthropic API
    # (used by any_llm) uses dashes ("claude-haiku-4-5"). OpenAI ids keep dots
    # (e.g. "gpt-4.1-mini"), so only rewrite for Anthropic.
    if ai_settings.provider == "anthropic":
        model = model.replace(".", "-")
    return model


def cms_get_provider(alias="default"):
    """Return the agent LLM provider config from the CMS, if configured."""
    # Imported lazily to avoid import-time / app-loading issues.
    from climweb.base.ai.backend import get_ai_settings

    ai_settings = get_ai_settings()
    if ai_settings is not None and ai_settings.is_configured():
        return {
            "provider": ai_settings.provider,  # "openai" or "anthropic"
            "model": _agent_model_id(ai_settings),
            "api_key": ai_settings.get_api_key(),
        }

    # Not configured — defer to wagtail-ai's own behaviour (PROVIDERS/env).
    if _original_get_provider is not None:
        return _original_get_provider(alias)
    raise RuntimeError("wagtail-ai get_provider was not patched correctly.")


def install_cms_provider():
    """Monkeypatch wagtail-ai's agent provider resolver to use the CMS key.

    Safe no-op if wagtail-ai (or its agents module) isn't installed.
    """
    global _original_get_provider
    try:
        from wagtail_ai.agents import base as agent_base
    except Exception:
        return  # wagtail-ai not installed / no agents module — nothing to do.

    # Avoid double-patching (e.g. if ready() runs more than once).
    if getattr(agent_base.get_provider, "_climweb_patched", False):
        return

    _original_get_provider = agent_base.get_provider
    cms_get_provider._climweb_patched = True
    agent_base.get_provider = cms_get_provider

    # get_llm_service caches the built client per alias; drop any cached client
    # so the next call uses our provider config.
    try:
        agent_base.get_llm_service.cache_clear()
    except Exception:
        pass

    logger.info("ClimWeb: patched wagtail_ai.agents.base.get_provider to use AISettings.")
