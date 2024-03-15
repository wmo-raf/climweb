from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.dates import MONTHS
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from forecastmanager.forecast_settings import ForecastSetting
from forecastmanager.models import City, CityForecast
from wagtail.admin.panels import MultiFieldPanel, FieldPanel
from wagtail.api.v2.utils import get_full_url
from wagtail.contrib.routable_page.models import RoutablePageMixin, route, path
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page

from base.mixins import MetadataPageMixin
from base.models import AbstractIntroPage
from base.utils import paginate, query_param_to_list
from .blocks import ExtremeWeatherBlock


class WeatherDetailPage(MetadataPageMixin, RoutablePageMixin, Page):
    template = "weather/weather_detail_page.html"
    max_count = 1

    parent_page_types = ["home.HomePage"]

    @path('')
    @path('daily-table/', name="daily_table")
    @path('daily-table/<str:city_slug>/', name="daily_table_for_city")
    def forecast_for_city(self, request, city_slug=None):
        context_overrides = {}
        fm_settings = ForecastSetting.for_request(request)
        city_detail_page = fm_settings.weather_detail_page
        city_detail_page_url = None

        if city_detail_page:
            city_detail_page = city_detail_page.specific
            city_detail_page_url = city_detail_page.get_full_url(request)
            city_detail_page_url = city_detail_page_url + city_detail_page.detail_page_base_url
            context_overrides.update({
                "city_detail_page_url": city_detail_page_url,
            })

        city_search_url = get_full_url(request, reverse("cities-list"))
        context_overrides.update({
            "city_search_url": city_search_url,
            "city_detail_page_url": city_detail_page_url
        })
        if city_slug:
            city = City.objects.filter(slug=city_slug).first()
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

    @property
    def detail_page_base_url(self):
        detail_base_url = self.reverse_subpage("daily_table")
        return detail_base_url


class DailyWeatherReportIndexPage(AbstractIntroPage):
    template = "weather/daily_weather_report_index.html"
    parent_page_types = ["weather.WeatherDetailPage"]
    max_count = 1

    weather_summary_heading = models.CharField(max_length=255, blank=True, null=True,
                                               default="Weather Summary for previous day",
                                               verbose_name=_("Weather summary section heading"))
    extremes_section_title = models.CharField(max_length=255, blank=True, null=True,
                                              default="Extreme weather observations",
                                              verbose_name=_("Extreme weather observations section title"))
    weather_forecast_heading = models.CharField(max_length=255, blank=True, null=True,
                                                default="Weather Forecast for next day",
                                                verbose_name=_("Weather forecast section heading"))

    items_per_page = models.PositiveIntegerField(default=6, validators=[
        MinValueValidator(6),
        MaxValueValidator(20),
    ], verbose_name=_("Products per page"), help_text=_(
        "Number of items to show in the list section. Default is 6. Maximum is 20."))

    content_panels = Page.content_panels + [
        *AbstractIntroPage.content_panels,
        FieldPanel('weather_summary_heading'),
        FieldPanel('extremes_section_title'),
        FieldPanel('weather_forecast_heading'),
        FieldPanel('items_per_page'),
    ]

    @cached_property
    def all_items(self):
        items = self.get_children().specific().live().order_by('-dailyweatherreportdetailpage__issued_on')
        # Return the related items
        return items

    def filter_items(self, request):
        items = self.all_items

        years = query_param_to_list(request.GET.get("year"), as_int=True)
        months = query_param_to_list(request.GET.get("month"), as_int=True)

        filters = models.Q()

        if years:
            filters &= models.Q(dailyweatherreportdetailpage__issued_on__year__in=years)
        if months:
            filters &= models.Q(dailyweatherreportdetailpage__issued_on__month__in=months)

        return items.filter(filters)

    def filter_and_paginate_items(self, request):
        page = request.GET.get('page')

        filtered_products = self.filter_items(request)

        paginated_products = paginate(filtered_products, page, self.items_per_page)

        return paginated_products

    @cached_property
    def filters(self):
        years = self.all_items.dates("dailyweatherreportdetailpage__issued_on", "year")
        return {'year': years, 'month': MONTHS}

    def get_context(self, request, *args, **kwargs):
        context = super(DailyWeatherReportIndexPage, self).get_context(request, *args, **kwargs)
        context['daily_weather_reports'] = self.filter_and_paginate_items(request)

        return context


class DailyWeatherReportDetailPage(MetadataPageMixin, Page):
    template = "weather/daily_weather_report_detail.html"

    parent_page_types = ["weather.DailyWeatherReportIndexPage"]

    issued_on = models.DateField(verbose_name=_("Issued on"),
                                 help_text=_("The date the report was issued."))

    summary_date = models.DateField(blank=True, null=True, verbose_name=_("Summary Date"))
    summary_description = RichTextField(blank=True, null=True, verbose_name=_('Weather Summary Description'))

    forecast_date = models.DateField(blank=True, null=True, verbose_name=_("Forecast Date"))
    forecast_description = RichTextField(blank=True, null=True, verbose_name=_('Weather Forecast Description'))

    extreme_weather_observations = StreamField([
        ('extremes', ExtremeWeatherBlock(label=_("Extreme Weather Observation"))),
    ], blank=True, null=True, use_json_field=True, verbose_name=_("Extreme weather observations from previous day"))

    content_panels = Page.content_panels + [
        FieldPanel('issued_on'),
        MultiFieldPanel([
            FieldPanel('summary_date'),
            FieldPanel('summary_description'),
            FieldPanel('extreme_weather_observations'),
        ], heading="Weather summary for previous day"),

        MultiFieldPanel([
            FieldPanel('forecast_date'),
            FieldPanel('forecast_description'),
        ], heading="Weather forecast for next day"),
    ]
