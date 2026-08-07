from typing import NamedTuple

from django.utils import timezone
from forecastmanager.forecast_settings import ForecastSetting
from forecastmanager.models import CityForecast
from wagtail.models import Site


def get_city_forecast_detail_data(city, multi_period=False, request=None, for_home_widget=False):
    localtime = timezone.localtime()
    city_forecasts = CityForecast.objects.filter(
        city=city, parent__forecast_date__gte=localtime.date()
    ).select_related('parent', 'condition').prefetch_related('data_values__parameter')

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

class ForecastSeries(NamedTuple):
    """
    A parameter's values across one day's forecasts, plus what they contained.

    ``has_numeric`` and ``has_text`` are not opposites: a day can hold both a
    plottable number and free text in different time slots, and it is that
    mixed case the graph flags need to distinguish.
    """
    values: list
    has_numeric: bool
    has_text: bool


def extract_forecast_metric_series(forecasts, param_slug):
    """
    Collect one parameter's values across a day's forecasts, in order.

    Empty and missing values become None (nothing was entered). Non-numeric
    values also become None, but are reported separately via ``has_text`` so
    callers can tell "the editor entered nothing" apart from "the editor
    entered something we cannot plot".
    """
    values = []
    has_numeric = False
    has_text = False

    for forecast in forecasts:
        raw_value = (forecast.data_values_dict.get(param_slug) or {}).get("value")

        if raw_value in (None, ''):
            values.append(None)
            continue

        try:
            values.append(float(raw_value))
            has_numeric = True
        except (TypeError, ValueError):
            values.append(None)
            has_text = True

    return ForecastSeries(values=values, has_numeric=has_numeric, has_text=has_text)


def series_is_plottable(series_by_slug, *param_slugs):
    """
    Decide whether a chart drawing ``param_slugs`` should be rendered at all.

    A chart is drawn only when at least one of its parameters has a number and
    none of them contain free text. Dropping the whole chart on any text value
    is deliberate: a text slot has to be plotted as a gap, and a gap is
    indistinguishable from missing data, so a partial curve would quietly
    misrepresent the forecast. The daily table above still shows the raw text,
    so nothing the editor entered is lost.
    """
    has_numeric = any(series_by_slug[slug].has_numeric for slug in param_slugs)
    has_text = any(series_by_slug[slug].has_text for slug in param_slugs)

    return has_numeric and not has_text
