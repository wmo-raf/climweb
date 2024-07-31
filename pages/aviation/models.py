import uuid
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _

from wagtailgeowidget.helpers import geosgeometry_str_to_struct
from wagtailgeowidget.panels import LeafletPanel, GeoAddressPanel
from wagtail_color_panel.edit_handlers import NativeColorPanel

from django_extensions.db.fields import AutoSlugField
from wagtailgeowidget import geocoders
from wagtail_color_panel.fields import ColorField
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel


class StationCategory(models.Model):
    name = models.CharField(_("Category name"), max_length=50)
    color = ColorField(blank=True, null=True, default="#363636",
                               help_text=_("Category color"))
    
    panels = [
        FieldPanel('name'),
        NativeColorPanel('color')
    ]
    class Meta:
        verbose_name = _("Station Category")
        verbose_name_plural = _("Station Categories")


    def __str__(self) -> str:
        return self.name

# Create your models here.
class Station(models.Model):
    id = models.CharField(unique=True, primary_key=True,)
    name = models.CharField(verbose_name=_("Station Name"), max_length=255, null=True, blank=False, unique=True)
    slug = AutoSlugField(populate_from='name', null=True, unique=True, default=None, editable=False)
    category = models.ForeignKey(StationCategory, verbose_name=_("Station Category"), on_delete=models.CASCADE)
    location = models.PointField(verbose_name=_("Station Location (Lat, Lng)"))
    
    
    panels = [
        FieldPanel("id"),
        GeoAddressPanel("name", geocoder=geocoders.NOMINATIM),
        FieldPanel("category"),
        LeafletPanel("location", address_field="name"),
    ]

    class Meta:
        verbose_name = _("Station")
        verbose_name_plural = _("Stations")
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def coordinates(self):
        location = geosgeometry_str_to_struct(str(self.location))
        return [float(location['x']), float(location['y'])]

    @property
    def x(self):
        return self.coordinates[0]

    @property
    def y(self):
        return self.coordinates[1]


class Message(models.Model):

    MSG_FORMAT_CHOICES = [
        ('METAR','METAR'),
        ('TAF','TAF'),
    ]

    station = models.ForeignKey(Station, verbose_name=_("Station"), on_delete=models.CASCADE)
    msg_encode = models.TextField(_("Message in Encoded Form"))
    msg_decode = models.JSONField(_("Decoded Message"), blank=True, null=True)
    msg_format = models.CharField(max_length=50, choices=MSG_FORMAT_CHOICES,
                                          verbose_name=_("Message Format"),)
    msg_datetime = models.DateTimeField(_("Message Datetime"), auto_now=False, auto_now_add=False, null=True)

