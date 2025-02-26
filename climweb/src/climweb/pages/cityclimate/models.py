from adminboundarymanager.models import AdminBoundarySettings
from django.db import models
from django.template.defaultfilters import truncatechars
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from forecastmanager.models import City
from modelcluster.fields import ParentalKey
from opentelemetry import trace
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.api.v2.utils import get_full_url
from wagtail.fields import StreamField, RichTextField
from wagtail.models import Page, Orderable

from climweb.base.mixins import MetadataPageMixin
from climweb.config.telemetry.utils import climweb_trace
from .blocks import LineChartBlock, BarChartBlock, AreaChartBlock
from ...base.utils import get_first_non_empty_p_string

tracer = trace.get_tracer(__name__)

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

tracer = trace.get_tracer(__name__)


class CityClimateDataPage(MetadataPageMixin, Page):
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
    
    @property
    def template_date_format(self):
        time_format = self.time_format
        
        # default date format
        date_format = "Y-m-d"
        
        if time_format == "day":
            date_format = 'd'  # Day (e.g., 01, 02, ..., 31)
        elif time_format == "dayandmonth":
            date_format = 'd M'  # Day and abbreviated month (e.g., 01 Jan)
        elif time_format == "month":
            date_format = 'M'  # Full month name (e.g., January)
        elif time_format == "monthandyear":
            date_format = 'M Y'  # Full month and year (e.g., January 2025)
        elif time_format == "year":
            date_format = 'Y'
        
        return date_format
    
    @climweb_trace(tracer)
    def get_context(self, request, *args, **kwargs):
        context = super(CityClimateDataPage, self).get_context(request, *args, **kwargs)
        cities = City.objects.all().filter(datavalue__isnull=False).distinct()
        
        abm_settings = AdminBoundarySettings.for_request(request)
        abm_extents = abm_settings.combined_countries_bounds
        boundary_tiles_url = get_full_url(request, abm_settings.boundary_tiles_url)
        
        context.update({
            "cities": cities,
            "cities_with_data_ids": [str(city.pk) for city in cities],
            "city_data_url": get_full_url(request, reverse("climate_data", args=(self.pk,))),
            "parameters": self.parameters,
            "months": MONTHS,
            "bounds": abm_extents,
            "boundary_tiles_url": boundary_tiles_url,
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
    
    def get_meta_image(self):
        meta_image = super().get_meta_image()
        
        if not meta_image:
            meta_image = self.get_parent().get_meta_image()
        
        return meta_image
    
    def get_meta_description(self):
        meta_description = super().get_meta_description()
        
        if not meta_description and self.description:
            p = get_first_non_empty_p_string(self.description)
            if p:
                # Limit the search meta desc to google's 160 recommended chars
                meta_description = truncatechars(p, 160)
        
        return meta_description


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
