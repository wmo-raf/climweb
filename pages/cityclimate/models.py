from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from forecastmanager.models import City
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import StreamField, RichTextField
from wagtail.models import Page, Orderable
import json
from .blocks import LineChartBlock, BarChartBlock, AreaChartBlock
from django.core.serializers.json import DjangoJSONEncoder

MONTHS = [
    {"name": "January", "num": 1},
    {"name": "February", "num": 2},
    {"name": "March", "num": 3},
    {"name": "April", "num": 4},
    {"name": "Mary", "num": 5},
    {"name": "June", "num": 6},
    {"name": "July", "num": 7},
    {"name": "August", "num": 8},
    {"name": "September", "num": 9},
    {"name": "October", "num": 10},
    {"name": "November", "num": 11},
    {"name": "December", "num": 12},
]


class CityClimateDataPage(Page):
    template = "cityclimate/city_climate_data_page.html"
    parent_page_types = ['home.HomePage']
    subpage_types = []
    show_in_menus_default = True

    PERIOD_CHOICES = (
        ("day", "Day - e.g '01' "),
        ("dayandmonth", "Day and Month - e.g '01 Jan' "),
        ("month", "Month - e.g 'Jan' "),
        ("monthandyear", "Month and year - e.g 'Jan 2023' "),
        ("year", "Year - e.g '2023'"),
    )

    description = RichTextField(null=True, blank=True, verbose_name=_("Description"),
                                features=["bold", "ul", "ol", "link", "superscript", "subscript"])
    time_format = models.CharField(max_length=100, choices=PERIOD_CHOICES, verbose_name=_("Time Format"),
                                   help_text=_("In none selected,the default format e.g '2023-01-01' will be used"),
                                   blank=True)

    filter_by_month = models.BooleanField(default=False, verbose_name=_("Filter by Month"))

    content_panels = Page.content_panels + [
        FieldPanel("description"),
        FieldPanel("time_format"),
        FieldPanel("filter_by_month"),
        InlinePanel("data_parameters", heading=_("Data Parameters"), label=_("Data Parameter")),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super(CityClimateDataPage, self).get_context(request, *args, **kwargs)

        cities = City.objects.all()


        context.update({
            "cities": cities,
            "city_data_url": request.build_absolute_uri(reverse("climate_data", args=(self.pk,))),
            "parameters": self.parameters,
            "months": MONTHS
        })

        return context

    @cached_property
    def parameters(self):
        params = []

        for param in self.data_parameters.all():
            if param.enabled:
                chart_config = {}
                for config in param.chart_config:
                    chart_config = config.value.config

                param_data = {
                    "slug": param.slug,
                    "name": param.name,
                    "chart_config": chart_config,
                }

                if param.units:
                    param_data.update({"units": param.units})

                params.append(param_data)
        return params


class DataParameter(Orderable):
    page = ParentalKey(CityClimateDataPage, on_delete=models.CASCADE, related_name="data_parameters")
    name = models.CharField(max_length=100, verbose_name=_("Parameter name"))
    units = models.CharField(max_length=100, null=True, blank=True, verbose_name=_("Units"))
    slug = models.CharField(max_length=150)
    enabled = models.BooleanField(default=True, verbose_name=_("Enabled"))

    chart_config = StreamField([
        ("line_chart", LineChartBlock(label=_("Line Chart"))),
        ("bar_chart", BarChartBlock(label=_("Bar Chart"))),
        ("area_chart", AreaChartBlock(label=_("Area Chart"))),
    ], null=True, blank=True,
        use_json_field=True,
        max_num=1, verbose_name=_("Chart Configuration"))

    panels = [
        FieldPanel("name"),
        FieldPanel("units"),
        FieldPanel("enabled"),
        FieldPanel("chart_config")
    ]

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        return super().save(*args, **kwargs)


class DataValue(Orderable):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    parameter = models.ForeignKey(DataParameter, on_delete=models.CASCADE)
    date = models.DateField()
    value = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.city.name} - {self.parameter.name}"
