from django.apps import AppConfig

class SiteSettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'site_settings'

    def ready(self) -> None:
        
        from wagtail.models import Site
        from site_settings.models import IntegrationSettings

        # Get the default site
        site = Site.objects.get(is_default_site=True)

        # Get the SiteSettings instance for the default site
        settings = IntegrationSettings.for_site(site)

        # Get the values of the reCAPTCHA keys
        RECAPTCHA_PUBLIC_KEY = settings.recaptcha_public_key
        RECAPTCHA_PRIVATE_KEY = settings.recaptcha_private_key

        return super().ready()

        
