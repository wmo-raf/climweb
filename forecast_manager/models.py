import uuid
import json
from django.utils.functional import cached_property
from django.contrib.gis.db import models
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel
from wagtailgeowidget.panels import LeafletPanel
from wagtailgeowidget.helpers import geosgeometry_str_to_struct


# Create your models here.
@register_snippet
class City(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique UUID. Auto generated on creation.",
    )
    name = models.CharField(verbose_name="City Name", max_length=255, null=True, blank=False,unique=True)
    location = models.PointField(verbose_name="City Location (Lat, Lng)")

    panels = [
        FieldPanel("name"),
        LeafletPanel("location"),
    ]

    class Meta:
        verbose_name = "City"
        verbose_name_plural = "Cities"

    def __str__(self) -> str:
        return self.name

    @cached_property
    def point(self):
        return json.dumps(geosgeometry_str_to_struct(str(self.location)))

    @property
    def lat(self):
        return self.point['y']

    @property
    def lng(self):
        return self.point['x']
 

@register_snippet
class ConditionCategory(models.Model):
    title = models.CharField(max_length=50, help_text="Weather Condition Title", verbose_name="Weather Condtion Title")
    # icon = models.ForeignKey(
    #     'wagtailimages.Image',
    #     verbose_name="Weather Condition Icon",
    #     help_text="An Icon representing the weather condtion",
    #     null=True,
    #     blank=True,
    #     on_delete=models.SET_NULL,
    #     related_name='+',
    # )
    
    description = models.CharField(max_length=250, blank=True, null=True)
    icon = models.ForeignKey(
        'webicons.WebIcon',
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    class Meta:
        verbose_name = "Weather Condition Category"
        verbose_name_plural = "Weather Condition Categories"

    
    def __str__(self):
        return self.title


class Forecast(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    forecast_date = models.DateField( auto_now=False, auto_now_add=False, verbose_name="Forecasts Date")
    max_temp = models.IntegerField(verbose_name="Maximum Temperature", blank=True)
    min_temp = models.IntegerField(verbose_name="Minimum Temperaure", blank=True)
    wind_direction = models.IntegerField(verbose_name="Wind Direction", blank=True, null=True)
    wind_speed = models.IntegerField(verbose_name="Wind Speed", blank=True, null=True)
    # condition = models.CharField(verbose_name="General Weather Condition", max_length=255, blank=True, help_text="E.g Light Showers", default="Light Showers")
    condition = models.ForeignKey(ConditionCategory, verbose_name="General Weather Condition", on_delete=models.CASCADE, help_text="E.g Light Showers")

    class Meta:
        verbose_name = "Forecast"
        verbose_name_plural = "Forecasts"
        constraints = [
            models.UniqueConstraint(fields=['city', 'forecast_date'], name='Unique combination of city and forecast date')
        ]

    panels = [
        FieldPanel("city"),
        FieldPanel("forecast_date"),
        FieldPanel("min_temp"),
        FieldPanel("max_temp"),
        FieldPanel("wind_direction"),
        FieldPanel("wind_speed"),
        FieldPanel("condition"),
    ]

    # def __str__(self):
    #     return f"{self.city} - {self.forecast_date}" 



    