import base64
import json
from django.http import HttpRequest
import requests
from climweb.pages.dashboards.forms import BoundaryIDWidget
from django.db import models
from django.contrib.gis.db import models as gis_models

from django.urls import reverse
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, TabbedInterface, ObjectList, Panel
from wagtail.snippets.models import register_snippet
from wagtail.fields import StreamField
from wagtail.models import Site
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

    
def get_absolute_url(path, request=None):
    """
    Build a full absolute URL from a relative path.
    Works without needing an incoming request.
    """
    if request:
        return request.build_absolute_uri(path)

    # Get Wagtail default site
    site = Site.objects.filter(is_default_site=True).first()
    if not site:
        raise RuntimeError("No default Wagtail Site is configured")

    domain = site.hostname
    port = site.port or 80
    scheme = "https" if port == 443 else "http"
    netloc = f"{domain}:{port}" if port not in [80, 443] else domain

    fake_request = HttpRequest()
    fake_request.META['HTTP_HOST'] = netloc
    fake_request.META['wsgi.url_scheme'] = scheme

    return fake_request.build_absolute_uri(path)


def get_gid_for_level(area_desc, level, request=None):
    """
    Given an area name and admin level, return the admin_path like:
    - /GH
    - /GH/GH11
    - /GH/GH11/GH1104

    Matches area_desc to name_{level} in /api/country responses.
    """

    if not area_desc or level is None:
        return None


    try:
        # Step 1: Get top-level countries
        base_url = get_absolute_url(reverse("country_list"), request)
        response = requests.get(base_url, timeout=5)
        response.raise_for_status()
        countries = response.json()

        for country in countries:
            if level == 0 and country.get("name_0") == area_desc:
                return f"/{country['gid_0']}"

            # Step 2: Get level 1 regions
            country_code = country["gid_0"]
            response_lvl1 = requests.get(f"{base_url}/{country_code}", timeout=5)
            response_lvl1.raise_for_status()
            level1_regions = response_lvl1.json()

            for region1 in level1_regions:
                if level == 1 and region1.get("name_1") == area_desc:
                    return f"/{region1['gid_0']}/{region1['gid_1']}"

                # Step 3: Get level 2 regions
                gid_1 = region1.get("gid_1")
                if gid_1:
                    response_lvl2 = requests.get(f"{base_url}/{country_code}/{gid_1}", timeout=5)
                    response_lvl2.raise_for_status()
                    level2_regions = response_lvl2.json()

                    for region2 in level2_regions:
                        if level == 2 and region2.get("name_2") == area_desc:
                            return f"/{region2['gid_0']}/{region2['gid_1']}/{region2['gid_2']}"

    except Exception as e:
        print("Error fetching gid for level:", e)

    return None


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
            "area_desc": self.instance.area_desc,
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

    area_desc = models.TextField(max_length=50,
                                help_text=_("The text describing the affected area of the alert message. Click on map to generate name"), null=True,  blank=True)
    admin_level = models.IntegerField(choices=ADMIN_LEVEL_CHOICES, default=0, help_text=_("Administrative Level"),  null=True, blank=False )
    
    geom = gis_models.MultiPolygonField(srid=4326, verbose_name=_("Area"), null=True,  blank=True)
    admin_path = models.CharField(null=True, max_length=250)

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
                FieldPanel("area_desc"),
                FieldPanel("geom", widget=BoundaryIDWidget(attrs={"resize_trigger_selector": ".w-tabs__tab.map-resize-trigger"}))
            ], heading=_("Admin Boundary"))
        ])
    ]

    def __str__(self):
        return f"{self.title} ({self.chart_type} chart) {self.area_desc}"
    

    def save(self, *args, **kwargs):
        if self.area_desc and self.admin_level is not None:
            self.admin_path = get_gid_for_level(self.area_desc, self.admin_level)
        super().save(*args, **kwargs)

    
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
        selected = self.dataset

        # Step 2: If it exists and has a dataset with a category, extract it
        if selected and hasattr(selected, "dataset") and selected.dataset and selected.dataset.category:
            dataset_category_title = selected.dataset.category.title


        menu_config = {"menuSection": "datasets", "datasetCategory": dataset_category_title}
        menu_str = json.dumps(menu_config, separators=(',', ':'))
        menu_bytes = menu_str.encode()
        menu_base64_bytes = base64.b64encode(menu_bytes)
        menu_byte_str = menu_base64_bytes.decode()

        return base_mapviewer_url + f"?map={map_byte_str}&mapMenu={menu_byte_str}"


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

    area_desc = models.TextField(max_length=50,
                                help_text=_("The text describing the affected area of the alert message"), null=True,  blank=True)
    admin_level = models.IntegerField(choices=ADMIN_LEVEL_CHOICES, default=1, help_text=_("Administrative Level"), blank=False )
    
    geom = gis_models.MultiPolygonField(srid=4326, verbose_name=_("Area"), null=True,  blank=True)
    admin_path = models.CharField(null=True, max_length=250)

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
            FieldPanel("area_desc"),
            FieldPanel("geom", widget=BoundaryIDWidget(attrs={"resize_trigger_selector": ".w-tabs__tab.map-resize-trigger"}))
            ], heading=_("Admin Boundary")),
        ]),
        
    ]

    def __str__(self):
        return f"{self.title} - {self.area_desc}"


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

    def save(self, *args, **kwargs):
        if self.area_desc and self.admin_level is not None:
            self.admin_path = get_gid_for_level(self.area_desc, self.admin_level)
        super().save(*args, **kwargs)