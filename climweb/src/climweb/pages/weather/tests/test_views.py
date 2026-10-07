from datetime import time, timedelta

from django.conf import settings
from django.contrib.gis.geos import Point
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from forecastmanager.forecast_settings import (
    ForecastDataParameters,
    ForecastPeriod,
    ForecastSetting,
    WeatherCondition,
)
from forecastmanager.models import City, CityForecast, DataValue, Forecast
from wagtail.models import Site


# The default settings use a manifest-backed static files storage, which raises
# for any static() lookup unless collectstatic has been run. The endpoint builds
# weather icon URLs with static(), so these tests use the plain storage.
PLAIN_STATIC_STORAGES = {
    **settings.STORAGES,
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


@override_settings(STORAGES=PLAIN_STATIC_STORAGES)
class TestHomeMapForecast(TestCase):
    """
    The home map forecast endpoint must answer in a fixed number of queries,
    however many cities, forecasts and parameters there are.
    """

    # Deliberately neither alphabetical nor reversed, so the ordering test can
    # tell "creation order" apart from a name sort.
    CITY_NAMES = ["Mombasa", "Kisumu", "Nairobi", "Lodwar", "Nakuru", "Eldoret"]

    def setUp(self):
        site = Site.objects.get(is_default_site=True)
        self.setting = ForecastSetting.for_site(site)

        # Start from a known-empty configuration regardless of any seeded rows.
        ForecastPeriod.objects.all().delete()
        ForecastDataParameters.objects.all().delete()
        WeatherCondition.objects.all().delete()

        self.condition = WeatherCondition.objects.create(
            parent=self.setting, symbol="sunny", label="Sunny"
        )
        self.parameters = [
            ForecastDataParameters.objects.create(
                parent=self.setting,
                parameter="max_temp",
                name="Max temp",
                parameter_type="numeric",
                parameter_unit="C",
            ),
            ForecastDataParameters.objects.create(
                parent=self.setting,
                parameter="humidity",
                name="Humidity",
                parameter_type="numeric",
                parameter_unit="%",
            ),
        ]
        self.periods = []
        self.forecasts = []
        self.cities = []

    def _create_periods(self, count):
        for t in [time(6, 0), time(18, 0)][:count]:
            self.periods.append(
                ForecastPeriod.objects.create(
                    parent=self.setting,
                    forecast_effective_time=t,
                    label=t.strftime("%H:%M"),
                )
            )

    def _add_forecast_day(self, offset):
        date = timezone.localtime().date() + timedelta(days=offset)
        for period in self.periods:
            self.forecasts.append(
                Forecast.objects.create(forecast_date=date, effective_period=period)
            )

    def _add_cities(self, count):
        for _ in range(count):
            index = len(self.cities)
            self.cities.append(
                City.objects.create(
                    name=self.CITY_NAMES[index],
                    location=Point(36.8 + index * 0.1, -1.0 - index * 0.1, srid=4326),
                )
            )

    def _fill(self):
        """Give every forecast a city forecast (with values) for every city."""
        for forecast in self.forecasts:
            for index, city in enumerate(self.cities):
                city_forecast, created = CityForecast.objects.get_or_create(
                    parent=forecast, city=city, defaults={"condition": self.condition}
                )
                if created:
                    DataValue.objects.create(
                        parent=city_forecast,
                        parameter=self.parameters[0],
                        value=str(20 + index),
                    )
                    DataValue.objects.create(
                        parent=city_forecast, parameter=self.parameters[1], value="60"
                    )

    def _fetch(self):
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(reverse("home-weather-forecast"))
        self.assertEqual(response.status_code, 200)
        return response.json(), len(ctx)

    def test_query_count_does_not_grow_with_cities_multi_period(self):
        self._create_periods(2)
        self._add_forecast_day(0)
        self._add_cities(2)
        self._fill()
        self._fetch()  # warm-up: one-off queries must not skew the comparison

        _, few = self._fetch()

        self._add_cities(4)
        self._fill()
        payload, many = self._fetch()

        self.assertTrue(payload["multi_period"])
        self.assertEqual([len(f["features"]) for f in payload["data"]], [6, 6])
        self.assertEqual(many, few)

    def test_query_count_does_not_grow_with_cities_or_days_single_period(self):
        self._create_periods(1)
        self._add_forecast_day(0)
        self._add_cities(2)
        self._fill()
        self._fetch()  # warm-up

        _, few = self._fetch()

        self._add_forecast_day(1)
        self._add_forecast_day(2)
        self._add_cities(4)
        self._fill()
        payload, many = self._fetch()

        self.assertFalse(payload["multi_period"])
        self.assertEqual([len(f["features"]) for f in payload["data"]], [6, 6, 6])
        self.assertEqual(many, few)

    def test_features_follow_creation_order_and_carry_values(self):
        self._create_periods(1)
        self._add_forecast_day(0)
        self._add_cities(len(self.CITY_NAMES))
        self._fill()

        payload, _ = self._fetch()

        (forecast,) = payload["data"]
        features = forecast["features"]
        self.assertEqual([f["properties"]["city"] for f in features], self.CITY_NAMES)

        first = features[0]["properties"]
        self.assertEqual(first["city_slug"], "mombasa")
        self.assertEqual(first["condition"], "sunny")
        self.assertEqual(first["max_temp"], 20.0)
        self.assertEqual(first["humidity"], 60.0)
        self.assertEqual(features[1]["properties"]["max_temp"], 21.0)
