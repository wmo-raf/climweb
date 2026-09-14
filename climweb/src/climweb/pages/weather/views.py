from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET
from django.template.loader import render_to_string
from forecastmanager.forecast_settings import ForecastSetting
from forecastmanager.models import City, Forecast
from forecastmanager.serializers import CitySerializer, ForecastSerializer
from wagtail.api.v2.utils import get_full_url
from wagtailcache.settings import wagtailcache_settings

from climweb.base.cache import wagcache
from climweb.pages.home.models import HomeMapSettings
from climweb.pages.weather.utils import (
    get_city_forecast_detail_data,
    get_city_slugs_with_forecast_data,
    get_home_widget_city_and_data,
)

@require_GET
def get_home_forecast_widget(request):
    city_slug = request.GET.get('city')

    # Keyed on what was asked for rather than on the city that ends up being
    # rendered: the default path may fall back to another city, and that
    # fallback response is still the right cached answer for the default path.
    cache_key = (
        f"city_forecast_widget_data_{city_slug}" if city_slug
        else "city_forecast_widget_data__home_default"
    )

    # Early cache check — skips all DB queries on a hit.
    if wagtailcache_settings.WAGTAIL_CACHE:
        cached = wagcache.get(cache_key)
        if cached is not None:
            return cached

    forecast_setting = ForecastSetting.for_request(request)
    forecast_periods_count = forecast_setting.periods.count()
    multi_period = forecast_periods_count > 1
    context = {}

    home_settings = HomeMapSettings.for_request(request)
    show_forecast_attribution = home_settings.show_forecast_attribution
    external_source = forecast_setting.enable_auto_forecast
    if external_source and show_forecast_attribution:
        source_name = "Yr.no"
        source_url = "https://www.yr.no"
        context.update({
            "external_source_attribution": _(
                "Forecast Data Source: %(forecast_source)s"
            ) % {"forecast_source": source_name},
            "external_source_url": source_url,
        })

    widget_data = None

    if city_slug:
        city = City.objects.filter(slug=city_slug).first()
        if city is None:
            # Return empty template response so JS detects no widget content
            # and shows the no-data state without triggering !response.ok
            return render(
                request,
                'weather/widgets/location_forecast_single_slider.html',
                {}   # empty context — city_forecasts_by_date missing → template renders nothing
            )
    else:
        # Nothing was asked for, so the widget picks: the default city when it
        # has data, otherwise the first city that does. Falling back matters
        # because an empty default city hides the widget outright instead of
        # showing a forecast for somewhere else.
        city, widget_data = get_home_widget_city_and_data(
            forecast_setting, multi_period=multi_period, request=request
        )

    if city is None:
        context.update({
            "error": True,
            "error_message": _("No location set in the system. Please contact the administrator."),
        })
        return render(request, 'weather/widgets/location_forecast_single_slider.html', context)

    city_detail_page = forecast_setting.weather_detail_page

    if city_detail_page:
        # Try getting the city detail page URL. If it fails, ignore it.
        # this is here because a different page than what is expected might be set
        try:
            city_detail_page = city_detail_page.specific
            city_detail_page_url = city_detail_page.get_full_url(request) + city_detail_page.reverse_subpage(
                "daily_table_for_city", kwargs={"city_slug": city.slug})
            context.update({
                "city_detail_page_url": city_detail_page_url,
            })
        except Exception:
            pass

    city_search_url = get_full_url(request, reverse("cities-list"))
    context.update({
        "city_search_url": city_search_url,
    })

    if forecast_setting.weather_reports_page:
        context.update({
            "weather_reports_page_url": forecast_setting.weather_reports_page.get_full_url(request)
        })

    # Already resolved alongside the city on the default path.
    if widget_data is None:
        widget_data = get_city_forecast_detail_data(city, multi_period=multi_period, request=request,
                                                    for_home_widget=True)

    context.update({
        "city": city,
        "show_condition_label": forecast_setting.show_conditions_label_on_widget,
        "use_period_labels": forecast_setting.use_period_labels,
        **widget_data,
    })

    if multi_period:
        response = render(request, 'weather/widgets/location_forecast_multiple_slider.html', context)
    else:
        response = render(request, 'weather/widgets/location_forecast_single_slider.html', context)

    if wagtailcache_settings.WAGTAIL_CACHE:
        wagcache.set(cache_key, response, 60 * 20)

    return response


@require_GET
def get_cities_with_forecast_data(request):
    """
    The slugs of cities that currently have a forecast to show.

    Used by the "use my location" lookup, which sorts cities by distance in the
    browser: without this it can only pick the nearest city outright, and lands
    on a no-data message whenever that one happens to be empty. Returning the
    answerable set lets it pick the nearest city that has something to say.

    Deliberately just slugs -- coordinates already come from the cities list
    endpoint, and this is fetched on page load wherever geolocation is granted.
    """
    forecast_setting = ForecastSetting.for_request(request)
    multi_period = forecast_setting.periods.count() > 1

    return JsonResponse({
        "slugs": sorted(get_city_slugs_with_forecast_data(multi_period=multi_period)),
    })


def get_home_map_forecast(request):
    forecast_setting = ForecastSetting.for_request(request)
    forecast_periods_count = forecast_setting.periods.count()
    
    multi_period = forecast_periods_count > 1
    
    if multi_period:
        forecasts = Forecast.objects.filter(forecast_date=timezone.localtime().date())
    else:
        forecasts = Forecast.objects.filter(forecast_date__gte=timezone.localtime().date())
    
    forecast_data = ForecastSerializer(forecasts, many=True, context={"request": request, }).data
    
    res_data = {
        "data": forecast_data,
        "multi_period": multi_period
    }
    
    return JsonResponse(res_data, safe=False)
