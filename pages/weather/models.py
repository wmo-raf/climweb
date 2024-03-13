from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from forecastmanager.forecast_settings import ForecastSetting
from forecastmanager.models import City, CityForecast
from wagtail.api.v2.utils import get_full_url
from wagtail.contrib.routable_page.models import path, RoutablePageMixin
from wagtail.models import Page

from base.mixins import MetadataPageMixin


class WeatherDetailPage(MetadataPageMixin, RoutablePageMixin, Page):
    template = "weather/weather_detail_page.html"
    max_count = 1

    parent_page_types = ["home.HomePage"]

    @path('')
    @path('<str:city_name>/')
    def forecast_for_city(self, request, city_name=None):
        context_overrides = {}
        fm_settings = ForecastSetting.for_request(request)
        city_detail_page = fm_settings.weather_detail_page
        city_detail_page_url = None

        if city_detail_page:
            city_detail_page = city_detail_page.specific
            city_detail_page_url = city_detail_page.get_full_url(request)
            city_detail_page_url = city_detail_page_url + city_detail_page.reverse_subpage("forecast_for_city")
            context_overrides.update({
                "city_detail_page_url": city_detail_page_url,
            })

        city_search_url = get_full_url(request, reverse("cities-list"))
        context_overrides.update({
            "city_search_url": city_search_url,
            "city_detail_page_url": city_detail_page_url
        })

        if city_name:
            city_name = city_name.replace("--", " ")
            city = City.objects.filter(name__iexact=city_name).first()
            if city is None:
                context_overrides.update({
                    "error": True,
                    "error_message": _("Location not found. Please search for a different location.")
                })

                return self.render(request, context_overrides=context_overrides)
        else:
            city = fm_settings.default_city
            if not city:
                city = City.objects.first()

        if city is None:
            context_overrides.update({
                "error": True,
                "error_message": _("No data found")
            })

            return self.render(request, context_overrides=context_overrides)

        city_forecasts = CityForecast.objects.filter(
            city=city,
            parent__forecast_date__gte=timezone.localtime()
        )

        city_forecasts_by_date = {}
        for forecast in city_forecasts:
            forecast_date = forecast.parent.forecast_date
            if forecast_date not in city_forecasts_by_date:
                city_forecasts_by_date[forecast_date] = []
            city_forecasts_by_date[forecast_date].append(forecast)

        weather_parameters = ForecastSetting.for_request(request).data_parameters.all()

        context_overrides.update({
            "city_forecasts_by_date": city_forecasts_by_date,
            "weather_parameters": weather_parameters,
            "city": city
        })

        return self.render(request, context_overrides=context_overrides)
