import logging

from django.test import RequestFactory
from forecastmanager.forecast_settings import ForecastSetting
from forecastmanager.models import City
from wagtail import hooks
from wagtail.models import Site
from wagtailcache.cache import clear_cache
from wagtailcache.settings import wagtailcache_settings

logger = logging.getLogger(__name__)


def _warm_forecast_widget_cache():
    """Re-render and cache the widget for the default city after a forecast update.

    This prevents the first real user request after a forecast change from hitting
    a cold cache and suffering the full DB + render cost.
    """
    if not wagtailcache_settings.WAGTAIL_CACHE:
        return

    try:
        site = Site.objects.get(is_default_site=True)
        forecast_setting = ForecastSetting.for_site(site)
        city = forecast_setting.default_city or City.objects.first()
        if city is None:
            return

        # Build a synthetic request so the view can resolve site-aware settings
        # and construct absolute URLs correctly.
        host = site.hostname
        if site.port not in (80, 443):
            host = f"{site.hostname}:{site.port}"

        request = RequestFactory().get(f"/?city={city.slug}", HTTP_HOST=host)

        from climweb.pages.weather.views import get_home_forecast_widget
        get_home_forecast_widget(request)

        logger.debug("Forecast widget cache warmed for city: %s", city.slug)
    except Exception:
        # Never let cache warming crash the hook or the forecast generation process.
        logger.exception("Failed to warm forecast widget cache")


@hooks.register("after_generate_forecast")
def after_generate_forecast(created_forecast_pks):
    clear_cache()
    _warm_forecast_widget_cache()


@hooks.register("after_clear_old_forecasts")
def after_clear_old_forecasts():
    clear_cache()


@hooks.register("after_forecast_add_from_form")
def after_forecast_add_from_form():
    clear_cache()
    _warm_forecast_widget_cache()
