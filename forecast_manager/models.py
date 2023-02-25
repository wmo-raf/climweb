import uuid

from django.contrib.gis.db import models
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel
from wagtailgeowidget.panels import LeafletPanel


# Create your models here.
@register_snippet
class City(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique UUID. Auto generated on creation.",
    )
    name = models.CharField(verbose_name="City Name", max_length=255, null=True, blank=False)
    location = models.PointField(verbose_name="City Location (Lat, Lng)")

    panels = [
        FieldPanel("name"),
        LeafletPanel("location"),
    ]
    
    def __str__(self):
        return f"{self.name}" 

    class Meta:
        verbose_name = "City"
        verbose_name_plural = "Cities"

# @register_snippet
class Forecast(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    forecast_date = models.DateField( auto_now=False, auto_now_add=False, verbose_name="Forecasts Date")
    max_temp = models.IntegerField(verbose_name="Maximum Temperature", blank=True)
    min_temp = models.IntegerField(verbose_name="Minimum Temperaure", blank=True)
    wind_direction = models.IntegerField(verbose_name="Wind Direction", blank=True)
    wind_speed = models.IntegerField(verbose_name="Wind Speed", blank=True)
    condition = models.CharField(verbose_name="General Weather Condition", max_length=255, null=True, blank=True, help_text="E.g Light Showers")

    class Meta:
        verbose_name = "Forecast"
        verbose_name_plural = "Forecasts"

    panels = [
        FieldPanel("city"),
        FieldPanel("forecast_date"),
        FieldPanel("min_temp"),
        FieldPanel("max_temp"),
        FieldPanel("wind_direction"),
        FieldPanel("wind_speed"),
        FieldPanel("condition"),
    ]

    def __str__(self):
        return f"{self.city} - {self.forecast_date}" 