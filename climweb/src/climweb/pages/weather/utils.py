from typing import NamedTuple

from django.utils import timezone
from forecastmanager.forecast_settings import ForecastSetting
from forecastmanager.models import City, CityForecast
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

def get_home_widget_city_and_data(forecast_setting, multi_period=False, request=None):
    """
    Pick the city the home forecast widget should show, and return its data.

    The configured default city wins whenever it has usable forecast data.
    When it does not -- a station that is behind on data entry, or a default
    that was chosen before any forecasts existed -- fall back to the first
    city that does. Without the fallback an empty default city takes the whole
    widget down with it: the home page drops the section server-side and the
    client-side render hides the wrapper, so visitors get a gap in the page
    rather than a forecast for some other location.

    Cities are tried in ``City`` order (alphabetical by name), so the fallback
    is stable between requests instead of being whichever row the database
    happens to return first.

    An explicitly requested city is never resolved through here -- a visitor
    who picked a location should be told that location has no forecast, not
    quietly shown a different one.

    Returns ``(city, data)``. ``city`` is ``None`` only when the system has no
    cities at all, and ``data`` then carries an empty ``city_forecasts_by_date``
    so callers can treat it like any other city with nothing to show.
    """
    default_city = forecast_setting.default_city or City.objects.first()

    default_city_data = None
    if default_city:
        default_city_data = get_city_forecast_detail_data(
            default_city, multi_period=multi_period, request=request, for_home_widget=True
        )
        if default_city_data.get("city_forecasts_by_date"):
            return default_city, default_city_data

    localtime = timezone.localtime()
    cities_with_forecasts = (
        CityForecast.objects
        .filter(parent__forecast_date__gte=localtime.date())
        .values_list("city_id", flat=True)
        .distinct()
    )

    for city in City.objects.filter(pk__in=cities_with_forecasts).order_by("name"):
        if default_city and city.pk == default_city.pk:
            continue

        city_data = get_city_forecast_detail_data(
            city, multi_period=multi_period, request=request, for_home_widget=True
        )

        # Holding a row that passes the date filter is not enough on
        # multi-period sites: get_city_forecast_detail_data also drops slots
        # whose time has already passed, so a candidate can still come back
        # empty late in the day. Ask it, rather than guessing from the query.
        if city_data.get("city_forecasts_by_date"):
            return city, city_data

    if default_city_data is not None:
        return default_city, default_city_data

    return None, {"city_forecasts_by_date": {}, "weather_parameters": []}


def get_city_slugs_with_forecast_data(multi_period=False):
    """
    Slugs of every city that currently has forecast data the widget would show.

    This exists so the browser can narrow "nearest city" down to cities that
    can actually answer. Picking the geometrically nearest city and hoping is
    what produced the dead end this replaces: a visitor asks for their
    location, the nearest city happens to be empty, and they get "No forecast
    data available" while a city slightly further out had a forecast all along.

    The filtering mirrors ``get_city_forecast_detail_data`` exactly, including
    the multi-period rule that drops slots whose time has already passed. A
    slug advertised here and then rejected by the widget view would put the
    visitor back at the message this is meant to avoid, so the two must agree.

    Non-multi-period sites answer from a single values query. Multi-period
    sites need the rows themselves, since ``datetime`` is composed per slot
    rather than stored, but it is still one query for every city at once.
    """
    localtime = timezone.localtime()
    upcoming = CityForecast.objects.filter(parent__forecast_date__gte=localtime.date())

    if not multi_period:
        return set(upcoming.values_list("city__slug", flat=True).distinct())

    slugs = set()
    for forecast in upcoming.select_related("parent", "city"):
        if forecast.datetime < localtime:
            continue
        slugs.add(forecast.city.slug)

    return slugs


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
