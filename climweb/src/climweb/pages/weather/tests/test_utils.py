from django.test import SimpleTestCase

from ..utils import extract_forecast_metric_series, series_is_plottable


class FakeForecast:
    def __init__(self, data_values_dict):
        self.data_values_dict = data_values_dict


def forecasts_with(*values, param_slug="wind_speed"):
    """Build one day's forecasts, one per time slot, for a single parameter."""
    return [FakeForecast({param_slug: {"value": value}}) for value in values]


class TestExtractForecastMetricSeries(SimpleTestCase):
    def test_numeric_values_are_floats_in_order(self):
        series = extract_forecast_metric_series(forecasts_with("25", "30.5"), "wind_speed")

        self.assertEqual(series.values, [25.0, 30.5])
        self.assertTrue(series.has_numeric)
        self.assertFalse(series.has_text)

    def test_free_text_is_flagged_and_nulled(self):
        # editors may enter ranges or qualifiers, since the field is free text
        for value in ("25-60, Max 60", "Max 60", "N/A", "--"):
            with self.subTest(value=value):
                series = extract_forecast_metric_series(forecasts_with(value), "wind_speed")

                self.assertEqual(series.values, [None])
                self.assertFalse(series.has_numeric)
                self.assertTrue(series.has_text)

    def test_blank_values_are_not_counted_as_text(self):
        series = extract_forecast_metric_series(forecasts_with("", None), "wind_speed")

        self.assertEqual(series.values, [None, None])
        self.assertFalse(series.has_numeric)
        self.assertFalse(series.has_text)

    def test_missing_parameter_yields_nulls(self):
        series = extract_forecast_metric_series([FakeForecast({})], "wind_speed")

        self.assertEqual(series.values, [None])
        self.assertFalse(series.has_numeric)
        self.assertFalse(series.has_text)

    def test_mixed_slots_keep_position(self):
        series = extract_forecast_metric_series(
            forecasts_with("22", "25-60, Max 60", "24"), "wind_speed"
        )

        self.assertEqual(series.values, [22.0, None, 24.0])
        self.assertTrue(series.has_numeric)
        self.assertTrue(series.has_text)

    def test_no_forecasts(self):
        series = extract_forecast_metric_series([], "wind_speed")

        self.assertEqual(series.values, [])
        self.assertFalse(series.has_numeric)
        self.assertFalse(series.has_text)


class TestSeriesIsPlottable(SimpleTestCase):
    def _series(self, *values, param_slug="wind_speed"):
        return extract_forecast_metric_series(forecasts_with(*values), param_slug)

    def test_fully_numeric_is_plottable(self):
        series_by_slug = {"wind_speed": self._series("22", "24")}

        self.assertTrue(series_is_plottable(series_by_slug, "wind_speed"))

    def test_any_text_drops_the_chart(self):
        # a partially plotted forecast would read as a complete one
        series_by_slug = {"wind_speed": self._series("22", "25-60, Max 60")}

        self.assertFalse(series_is_plottable(series_by_slug, "wind_speed"))

    def test_all_blank_is_not_plottable(self):
        series_by_slug = {"wind_speed": self._series("", None)}

        self.assertFalse(series_is_plottable(series_by_slug, "wind_speed"))

    def test_blanks_alongside_numbers_are_still_plottable(self):
        # a genuinely empty slot is an honest gap, unlike an unplottable value
        series_by_slug = {"wind_speed": self._series("22", "")}

        self.assertTrue(series_is_plottable(series_by_slug, "wind_speed"))

    def test_text_in_any_parameter_drops_a_multi_series_chart(self):
        series_by_slug = {
            "wind_speed": self._series("22", "24"),
            "wind_from_direction": self._series("180", "Variable"),
        }

        self.assertFalse(
            series_is_plottable(series_by_slug, "wind_speed", "wind_from_direction")
        )

    def test_multi_series_chart_needs_only_one_parameter_with_numbers(self):
        series_by_slug = {
            "air_temperature_max": self._series("30", "31"),
            "air_temperature_min": self._series("", ""),
        }

        self.assertTrue(
            series_is_plottable(series_by_slug, "air_temperature_max", "air_temperature_min")
        )
