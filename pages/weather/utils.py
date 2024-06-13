from django.utils import timezone
from forecastmanager.forecast_settings import ForecastSetting
from forecastmanager.models import CityForecast
from wagtail.models import Site


def get_city_forecast_detail_data(city, request=None):
    city_forecasts = CityForecast.objects.filter(
        city=city,
        parent__forecast_date__gte=timezone.localtime()
    )

    city_forecasts_by_date = {}
    current_datetime = timezone.localtime().replace(minute=0, second=0, microsecond=0)

    for forecast in city_forecasts:
        if forecast.datetime < current_datetime:
            continue

        forecast_date = forecast.parent.forecast_date
        if forecast_date not in city_forecasts_by_date:
            city_forecasts_by_date[forecast_date] = []
        city_forecasts_by_date[forecast_date].append(forecast)

    if request:
        weather_parameters = ForecastSetting.for_request(request).data_parameters.all()
    else:
        site = Site.objects.get(is_default_site=True)
        weather_parameters = ForecastSetting.for_site(site).data_parameters.all()

    return {
        "city_forecasts_by_date": city_forecasts_by_date,
        "weather_parameters": weather_parameters,
    }
