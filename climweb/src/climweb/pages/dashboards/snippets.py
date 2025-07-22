from django.db import models
from django.urls import reverse
from wagtail.admin.panels import FieldPanel,MultiFieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.fields import StreamField
from django.utils.translation import gettext_lazy as _
from climweb.base import blocks as climweb_blocks
from wagtail_color_panel.edit_handlers import NativeColorPanel
from django.utils.functional import cached_property
from wagtail.api.v2.utils import get_full_url
from adminboundarymanager.models import AdminBoundarySettings

from geomanager.models import RasterFileLayer, WmsLayer, VectorTileLayer

@register_snippet
class ChartSnippet(models.Model):
    CHART_TYPE_CHOICES = [
        ("line", "Line Chart"),
        ("column", "Bar Chart"),
        ("stripes", "Warming stripes"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    dataset = models.ForeignKey(
        "geomanager.RasterFileLayer", on_delete=models.CASCADE, related_name="charts"
    )
    data_unit = models.CharField(max_length=255, blank=True)

    chart_type = models.CharField(max_length=10, choices=CHART_TYPE_CHOICES, default="line")
    chart_color = models.CharField(
        max_length=7,
        default="#0b76e1",
        help_text="Hex color code for chart color (e.g., #0b76e1)"
    )

    panels = [
        FieldPanel("title"),
        FieldPanel("description"),
        MultiFieldPanel([
            FieldPanel("dataset"),
            FieldPanel("data_unit"),
        ],heading= "Data Configuration"),
        MultiFieldPanel([
            FieldPanel("chart_type"),
            NativeColorPanel("chart_color"),
        ], heading= "Chart Configuration"),
    ]

    def __str__(self):
        return f"{self.title} ({self.chart_type} chart)"

    class Meta:
        verbose_name = "Dashboard Chart"
        verbose_name_plural = "Dashboard Charts"


@register_snippet
class DashboardMap(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    map_layer = StreamField([
        ('raster_file_layer', climweb_blocks.UUIDModelChooserBlock(RasterFileLayer, icon="map")),
        ('wms_layer', climweb_blocks.UUIDModelChooserBlock(WmsLayer, icon="map")),
        ('vector_tile_layer', climweb_blocks.UUIDModelChooserBlock(VectorTileLayer, icon="map")),
    ], null=True, blank=False, max_num=1, verbose_name=_("Map Layers"))

    panels = [
        FieldPanel("title"),
        FieldPanel("description"),
        FieldPanel("map_layer"),
    ]

    def __str__(self):
        return self.title


    def get_layertimestampsurl(self, request):
        try:
            return get_full_url(request, reverse("layerrasterfile-list"))
        except Exception:
            return None

    def get_datasetsurl(self, request):
        try:
            return get_full_url(request, reverse("datasets-list"))
        except Exception:
            return None

    def get_boundary_tiles_url(self, request):
        try:
            abm_settings = AdminBoundarySettings.for_request(request)
            return get_full_url(request, abm_settings.boundary_tiles_url)
        except Exception:
            return None

    def get_bounds(self, request):
        try:
            abm_settings = AdminBoundarySettings.for_request(request)
            return abm_settings.combined_countries_bounds
        except Exception:
            return None


    @cached_property
    def selected_layer(self):
        """
        Returns the actual model instance (RasterFileLayer, WmsLayer, or VectorTileLayer)
        for the single layer selected in the StreamField.
        """
        if not self.map_layer or len(self.map_layer) == 0:
            return None

        return self.map_layer  # Already a model instance via UUIDModelChooserBlock

    @cached_property
    def map_layers_list(self):
        """
        Returns a list with one dict containing the selected layer instance.
        """
        layer = self.selected_layer
        if layer:
            return [{"layer": layer}]
        return []
