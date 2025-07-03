from django.db import models
from wagtail.admin.panels import FieldPanel,MultiFieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.fields import StreamField
from django.utils.translation import gettext_lazy as _
from climweb.base import blocks as climweb_blocks
from wagtail_color_panel.edit_handlers import NativeColorPanel

from geomanager.models import RasterFileLayer, WmsLayer, VectorTileLayer

@register_snippet
class ChartSnippet(models.Model):
    CHART_TYPE_CHOICES = [
        ("line", "Line Chart"),
        ("bar", "Bar Chart"),
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
        return f"{self.dataset.title} ({self.chart_type} chart)"

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

        return f"{self.title}"

    class Meta:
        verbose_name = "Dashboard Map"
        verbose_name_plural = "Dashboard Maps"