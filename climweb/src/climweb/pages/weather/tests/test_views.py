import json
from datetime import time, timedelta
from unittest import mock

from django.contrib.gis.geos import Point
from django.core.cache.backends.locmem import LocMemCache
from django.db import connection
from django.test import RequestFactory, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from forecastmanager.forecast_settings import (
    ForecastDataParameters,
    ForecastPeriod,
    ForecastSetting,
    WeatherCondition,
)
from forecastmanager.models import City, CityForecast, DataValue, Forecast
from wagtail.models import Site

from climweb.pages.weather import signals, views
from climweb.pages.weather.utils import (
    get_city_forecast_detail_data,
    get_city_slugs_with_forecast_data,
    get_home_widget_city_and_data,
)


class ForecastDataTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        site = Site.objects.get(is_default_site=True)
        setting = ForecastSetting.for_site(site)

        cls.period = ForecastPeriod.objects.create(parent=setting, forecast_effective_time=time(6, 0), label="Morning")
        cls.condition = WeatherCondition.objects.create(parent=setting, symbol="clearsky_day", label="Clear sky")
        cls.parameters = [
            ForecastDataParameters.objects.create(parent=setting, parameter=slug, name=slug)
            for slug in ("air_temperature_max", "air_temperature_min", "precipitation_amount")
        ]
        cls.today = timezone.localtime().date()

    def add_forecast(self, cities, status=Forecast.STATUS_PUBLISHED, forecast_date=None):
        forecast = Forecast.objects.create(
            forecast_date=forecast_date or self.today, effective_period=self.period, status=status
        )

        for i in range(cities):
            city = City.objects.create(name=f"City {forecast.pk}-{i}", location=Point(36.8 + i, -1.3))
            city_forecast = CityForecast.objects.create(parent=forecast, city=city, condition=self.condition)
            for parameter in self.parameters:
                DataValue.objects.create(parent=city_forecast, parameter=parameter, value="20")

        return forecast


class TestHomeMapForecast(ForecastDataTestCase):
    def get(self):
        request = RequestFactory().get("/api/home-weather-forecast/")
        return views.get_home_map_forecast(request)

    def count_queries(self):
        with CaptureQueriesContext(connection) as ctx:
            response = self.get()
        return len(ctx.captured_queries), json.loads(response.content)

    def test_query_count_does_not_grow_with_cities(self):
        self.add_forecast(cities=2)
        few_cities_queries, _ = self.count_queries()

        Forecast.objects.all().delete()
        self.add_forecast(cities=10)
        many_cities_queries, data = self.count_queries()

        self.assertEqual(len(data["data"][0]["features"]), 10)
        self.assertEqual(few_cities_queries, many_cities_queries)

    def test_draft_forecasts_are_not_served(self):
        self.add_forecast(cities=1, status=Forecast.STATUS_DRAFT)

        _, data = self.count_queries()

        self.assertEqual(data["data"], [])

    @override_settings(WAGTAIL_CACHE=True)
    def test_cached_response_is_cleared_when_forecast_changes(self):
        cache = LocMemCache("home-map-forecast-test", {})
        self.add_forecast(cities=1)

        with mock.patch.object(views, "wagcache", cache), mock.patch.object(signals, "wagcache", cache):
            first = json.loads(self.get().content)

            # served from cache: no queries at all
            with self.assertNumQueries(0):
                self.get()

            DataValue.objects.filter(parameter__parameter="air_temperature_max").update(value="31")
            # a bulk update sends no signal, so the cached copy is still served
            self.assertEqual(json.loads(self.get().content), first)

            # a normal save clears the cache and the new value shows
            data_value = DataValue.objects.filter(parameter__parameter="air_temperature_max").first()
            data_value.save()

            feature = json.loads(self.get().content)["data"][0]["features"][0]
            self.assertEqual(feature["properties"]["air_temperature_max"], 31.0)


class TestDraftForecastsAreHidden(ForecastDataTestCase):
    """The home widget, city detail pages and the "use my location" lookup all
    read through weather.utils; none of them may show a forecast still in review."""

    def setUp(self):
        self.draft = self.add_forecast(cities=1, status=Forecast.STATUS_DRAFT)
        self.draft_city = self.draft.city_forecasts.get().city

    def test_city_detail_data_skips_drafts(self):
        data = get_city_forecast_detail_data(self.draft_city)

        self.assertEqual(data["city_forecasts_by_date"], {})

    def test_city_detail_data_keeps_published(self):
        self.draft.status = Forecast.STATUS_PUBLISHED
        self.draft.save()

        data = get_city_forecast_detail_data(self.draft_city)

        self.assertEqual(list(data["city_forecasts_by_date"]), [self.today])

    def test_cities_with_forecast_data_skips_drafts(self):
        self.assertEqual(get_city_slugs_with_forecast_data(), set())
        self.assertEqual(get_city_slugs_with_forecast_data(multi_period=True), set())

    def test_home_widget_does_not_fall_back_to_a_draft_city(self):
        # one forecast per date and period, so the published one goes on tomorrow
        published = self.add_forecast(cities=1, forecast_date=self.today + timedelta(days=1))
        published_city = published.city_forecasts.get().city

        setting = ForecastSetting.for_site(Site.objects.get(is_default_site=True))
        setting.default_city = None

        # cities are tried alphabetically, so make the draft city come first
        self.draft_city.name = "AAA draft city"
        self.draft_city.save()

        city, data = get_home_widget_city_and_data(setting)

        self.assertEqual(city, published_city)
