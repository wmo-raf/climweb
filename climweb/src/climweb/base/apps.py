from django.apps import AppConfig


class BaseConfig(AppConfig):
    name = 'climweb.base'

    def ready(self):
        from .choosers import searchable_viewset_factory
        import wagtailmodelchooser.viewsets as _wmc_viewsets
        import wagtailmodelchooser.blocks as _wmc_blocks

        # Patch both the module attribute and the already-imported reference in
        # blocks.py so SearchableChooser's custom view classes are respected by
        # both the admin viewset hook and the StreamField block widget.
        _wmc_viewsets.viewset_factory = searchable_viewset_factory
        _wmc_blocks.viewset_factory = searchable_viewset_factory

        # Make wagtail-ai's agent features (content feedback, image alt-text,
        # related pages, title/description field panels) use the per-site
        # encrypted key from AISettings instead of a PROVIDERS/env key.
        from climweb.base.ai.agent_provider import install_cms_provider
        install_cms_provider()
