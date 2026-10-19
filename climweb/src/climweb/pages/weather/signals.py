from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from climweb.base.cache import wagcache
from climweb.pages.weather.views import get_home_map_forecast_cache_key


@receiver(post_save)
@receiver(post_delete)
def clear_home_map_forecast_cache(sender, **kwargs):
    """
    Drop the cached home map forecast whenever any forecastmanager model changes.

    Forecasts, their city values, periods, conditions, cities and the forecast
    settings all feed the map, so a forecaster's correction should show up
    straight away rather than after the cache times out.

    Bulk writes (bulk_create, queryset.update) send no signals; those are
    covered by the cache timeout.
    """
    if sender._meta.app_label != "forecastmanager":
        return

    wagcache.delete(get_home_map_forecast_cache_key(timezone.localtime().date()))
