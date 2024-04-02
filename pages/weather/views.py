from django.shortcuts import render

from django.urls import reverse
from django.utils import timezone
from forecastmanager.forecast_settings import ForecastSetting
from forecastmanager.models import City, CityForecast
from wagtail.api.v2.utils import get_full_url
from wagtail.models import Site


def get_home_forecast_widget(request):
    context = {}

    site = Site.objects.get(is_default_site=True)
    forecast_setting = ForecastSetting.for_site(site)

    city_detail_page = forecast_setting.weather_detail_page
    city_detail_page_url = None

    if city_detail_page:
        city_detail_page = city_detail_page.specific
        all_city_detail_page_url = city_detail_page.get_full_url(request)
        city_detail_page_url = all_city_detail_page_url + city_detail_page.detail_page_base_url
        context.update({
            "all_city_detail_page_url": all_city_detail_page_url,
            "city_detail_page_url": city_detail_page_url,

        })

    city_search_url = get_full_url(request, reverse("cities-list"))
    context.update({
        "city_search_url": city_search_url,
        "city_detail_page_url": city_detail_page_url
    })

    if forecast_setting.weather_reports_page:
        context.update({
            "weather_reports_page_url": forecast_setting.weather_reports_page.get_full_url(request)
        })

    default_city = forecast_setting.default_city
    if not default_city:
        default_city = City.objects.first()

    if default_city:
        default_city_forecasts = CityForecast.objects.filter(
            city=default_city,
            parent__forecast_date__gte=timezone.localtime(),
            parent__effective_period__default=True
        ).order_by("parent__forecast_date")

        # get unique forecast dates
        forecast_dates = default_city_forecasts.values_list("parent__forecast_date", flat=True).distinct()

        context.update({
            "default_city_forecasts": default_city_forecasts,
            "forecast_dates": forecast_dates,
        })

    return render(request, 'home/forecast_widget_include.html', context)
