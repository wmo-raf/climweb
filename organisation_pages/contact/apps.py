from django.apps import AppConfig


class ContactConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'organisation_pages.contact'

    def ready(self):
        
        from django.utils.functional import lazy
        from wagtail.models import Site
        from site_settings.models import IntegrationSettings

        site = Site.objects.get(is_default_site=True)

        # Get the SiteSettings instance for the default site
        settings = IntegrationSettings.for_site(site)

        RECAPTCHA_PUBLIC_KEY = settings.recaptcha_public_key
        RECAPTCHA_PRIVATE_KEY = settings.recaptcha_private_key
        NOCAPTCHA = True

