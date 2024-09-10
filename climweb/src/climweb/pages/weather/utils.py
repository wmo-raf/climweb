from django.utils import timezone
from forecastmanager.forecast_settings import ForecastSetting
from forecastmanager.models import CityForecast
from wagtail.models import Site


def get_city_forecast_detail_data(city, multi_period=False, request=None, for_home_widget=False):
    localtime = timezone.localtime()

    city_forecasts = CityForecast.objects.filter(city=city, parent__forecast_date__gte=localtime.date())

    city_forecasts_by_date = {}

    for forecast in city_forecasts:
        if multi_period and forecast.datetime < localtime:
            continue

        forecast_date = forecast.parent.forecast_date
        if forecast_date not in city_forecasts_by_date:
            city_forecasts_by_date[forecast_date] = []
        city_forecasts_by_date[forecast_date].append(forecast)
    if request:
        forecast_setting = ForecastSetting.for_request(request)
    else:
        site = Site.objects.get(is_default_site=True)
        forecast_setting = ForecastSetting.for_site(site)

    if for_home_widget:
        weather_parameters = forecast_setting.data_parameters.filter(show_on_home_widget=True)[:4]
    else:
        weather_parameters = forecast_setting.data_parameters.all()

    return {
        "city_forecasts_by_date": city_forecasts_by_date,
        "weather_parameters": weather_parameters,
    }
