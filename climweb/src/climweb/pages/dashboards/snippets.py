import base64
import json
from climweb.pages.dashboards.forms import BoundaryIDWidget
from django.db import models
from django.contrib.gis.db import models as gis_models

from django.urls import reverse
from wagtail.admin.panels import FieldPanel,MultiFieldPanel,TabbedInterface,ObjectList
from wagtail.snippets.models import register_snippet
from wagtail.fields import StreamField
from django.utils.translation import gettext_lazy as _
from climweb.base import blocks as climweb_blocks
from wagtail_color_panel.edit_handlers import NativeColorPanel
from django.utils.functional import cached_property
from wagtail.api.v2.utils import get_full_url
from adminboundarymanager.models import AdminBoundarySettings

from geomanager.models import RasterFileLayer, WmsLayer, RasterTileLayer, VectorTileLayer
from shapely.geometry import shape
from shapely import Point, Polygon
from wagtailmodelchooser import register_model_chooser


register_model_chooser(RasterFileLayer)
register_model_chooser(WmsLayer)
register_model_chooser(RasterTileLayer)
register_model_chooser(VectorTileLayer)

class DashboardMapValue:
    def __init__(self, instance):
        self.instance = instance

    @cached_property
    def area(self):
        geom_geojson_str = self.instance.boundary
        geom_geojson_dict = json.loads(geom_geojson_str)
        geom_shape = shape(geom_geojson_dict)

        polygons = []
        if isinstance(geom_shape, Polygon):
            polygons.append(geom_shape)
        else:
            polygons = list(geom_shape.geoms)

        polygons_data = []
        for polygon in polygons:
            coords = " ".join(["{},{}".format(y, x) for x, y in list(polygon.exterior.reverse().coords)])
            polygons_data.append(coords)

        area_data = {
            "type": "polygon",
            "areaDesc": self.instance.areaDesc,
            "polygons": polygons_data,
        }

        if getattr(self.instance, "altitude", None):
            area_data["altitude"] = self.instance.altitude
            if getattr(self.instance, "ceiling", None):
                area_data["ceiling"] = self.instance.ceiling

        if getattr(self.instance, "geocode", None):
            area_data["geocode"] = [
                {"valueName": g["valueName"], "value": g["value"]}
                for g in self.instance.geocode
            ]

        return area_data

    @cached_property
    def geojson(self):
        return json.loads(self.instance.boundary)

@register_snippet
class ChartSnippet(models.Model):
    CHART_TYPE_CHOICES = [
        ("line", "Line Chart"),
        ("column", "Bar Chart"),
        ("stripes", "Warming stripes"),
    ]

    ADMIN_LEVEL_CHOICES = (
        (0, _("Level 0")),
        (1, _("Level 1")),
        (2, _("Level 2")),
        (3, _("Level 3"))
    )

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

    areaDesc = models.TextField(max_length=50,
                                help_text=_("The text describing the affected area of the alert message"), null=True,  blank=True)
    admin_level = models.IntegerField(choices=ADMIN_LEVEL_CHOICES, default=0, help_text=_("Administrative Level"),  null=True, blank=True )
    
    geom = gis_models.MultiPolygonField(srid=4326, verbose_name=_("Area"), null=True,  blank=True)

    panels = [
        TabbedInterface([
            ObjectList([
                FieldPanel("title"),
                FieldPanel("description"),
                MultiFieldPanel([
                    FieldPanel("dataset"),
                    FieldPanel("data_unit"),
                ],heading= "Data Configuration"),
                MultiFieldPanel([
                    FieldPanel("chart_type"),
                    NativeColorPanel("chart_color"),
                ], heading= "Chart Configuration")
            ], heading=_("Layer")),
            ObjectList([
                FieldPanel("admin_level"),
                FieldPanel("areaDesc"),
                FieldPanel("geom", widget=BoundaryIDWidget(attrs={"resize_trigger_selector": ".w-tabs__tab.map-resize-trigger"}))
            ], heading=_("Admin Boundary"))
        ])
    ]

    def __str__(self):
        return f"{self.title} ({self.chart_type} chart)"

    class Meta:
        verbose_name = "Dashboard Chart"
        verbose_name_plural = "Dashboard Charts"


@register_snippet
class DashboardMap(models.Model):

    ADMIN_LEVEL_CHOICES = (
        (0, _("Level 0")),
        (1, _("Level 1")),
        (2, _("Level 2")),
        (3, _("Level 3"))
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    areaDesc = models.TextField(max_length=50,
                                help_text=_("The text describing the affected area of the alert message"), null=True,  blank=True)
    admin_level = models.IntegerField(choices=ADMIN_LEVEL_CHOICES, default=1, help_text=_("Administrative Level"), blank=False )
    
    geom = gis_models.MultiPolygonField(srid=4326, verbose_name=_("Area"), null=True,  blank=True)

    map_layer = StreamField([
        ('raster_file_layer', climweb_blocks.UUIDModelChooserBlock(RasterFileLayer, icon="map")),
        ('wms_layer', climweb_blocks.UUIDModelChooserBlock(WmsLayer, icon="map")),
        ('raster_tile_layer', climweb_blocks.UUIDModelChooserBlock(RasterTileLayer, icon="map")),
        ('vector_tile_layer', climweb_blocks.UUIDModelChooserBlock(VectorTileLayer, icon="map")),
    ], null=True, blank=False, max_num=1, verbose_name=_("Map Layers"))

    panels = [
        TabbedInterface([
            ObjectList([
                
                FieldPanel("title"),
                FieldPanel("description"),
                FieldPanel("map_layer"),
            ], heading=_("Layer")),
            ObjectList([
                FieldPanel("admin_level"),
            FieldPanel("areaDesc"),
            FieldPanel("geom", widget=BoundaryIDWidget(attrs={"resize_trigger_selector": ".w-tabs__tab.map-resize-trigger"}))
            ], heading=_("Admin Boundary")),
        ]),
        
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

    @property
    def mapviewer_map_url(self):
        base_mapviewer_url = reverse("mapview")

        map_config = {
            "datasets": [{"dataset": "political-boundaries", "layers": ["political-boundaries"], "visibility": True}]
        }

        map_str = json.dumps(map_config, separators=(',', ':'))

        map_bytes = map_str.encode()
        map_base64_bytes = base64.b64encode(map_bytes)
        map_byte_str = map_base64_bytes.decode()

        dataset_category_title = "Unknown"

        # Step 1: Get selected layer instance (already a model via UUIDModelChooserBlock)
        selected = self.selected_layer

        # Step 2: If it exists and has a dataset with a category, extract it
        if selected and hasattr(selected, "dataset") and selected.dataset and selected.dataset.category:
            dataset_category_title = selected.dataset.category.title


        menu_config = {"menuSection": "datasets", "datasetCategory": dataset_category_title}
        menu_str = json.dumps(menu_config, separators=(',', ':'))
        menu_bytes = menu_str.encode()
        menu_base64_bytes = base64.b64encode(menu_bytes)
        menu_byte_str = menu_base64_bytes.decode()

        return base_mapviewer_url + f"?map={map_byte_str}&mapMenu={menu_byte_str}"
        

    @property
    def geom_geojson(self):
        if self.geom:
            return self.geom.geojson  # returns valid GeoJSON string
        return None
        

    @cached_property
    def boundary_tiles_url(self):
        return reverse("admin_boundary_tiles", args=[0, 0, 0]).replace("/0/0/0", r"/{z}/{x}/{y}")
    
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
