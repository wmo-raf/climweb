import base64
import json
import uuid
from climweb.pages.dashboards.blocks import ChartVariableBlock
from rest_framework.exceptions import NotFound
from django.contrib.gis.geos import MultiPolygon

from climweb.pages.dashboards.forms import BoundaryIDWidget
from django.db import models
from django.contrib.gis.db import models as gis_models
from climweb.config.settings.base import SUMMARY_RICHTEXT_FEATURES

from django.core.exceptions import ValidationError
from django.urls import reverse
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, TabbedInterface, ObjectList, Panel
from wagtail.snippets.models import register_snippet
from wagtail.fields import StreamField, RichTextField
from wagtail.models import Site
from django.utils.translation import gettext_lazy as _
from climweb.base import blocks as climweb_blocks
from wagtail_color_panel.edit_handlers import NativeColorPanel
from django.utils.functional import cached_property
from wagtail.api.v2.utils import get_full_url
from adminboundarymanager.models import AdminBoundarySettings

from geomanager.models import RasterFileLayer, WmsLayer, RasterTileLayer, VectorTileLayer
from shapely.geometry import shape
from shapely import Polygon
from wagtailmodelchooser import register_model_chooser
from adminboundarymanager.models import AdminBoundary
from geomanager.models import Geostore


register_model_chooser(RasterFileLayer)
register_model_chooser(WmsLayer)
register_model_chooser(RasterTileLayer)
register_model_chooser(VectorTileLayer)

    
ADMIN_LEVEL_CHOICES = (
    (0, _("Level 0")),
    (1, _("Level 1")),
    (2, _("Level 2")),
)

def get_by_admin(gid_0, gid_1=None, gid_2=None, simplify_thresh=None):
    abm_settings = AdminBoundarySettings.objects.first()
    if not abm_settings:
        raise RuntimeError("No default AdminBoundarySettings configured")

    data_source = abm_settings.data_source

    countries = AdminBoundary.objects.filter(level=0).filter(gid_0=gid_0)
    if not countries.exists():
        return None
    
    country_iso = countries.values_list("gid_0", flat=True).first()

    geostore_filter = {
        "iso": country_iso,
        "id1": None,
        "id2": None,
    }

    boundary_filter = {
            "gid_0": gid_0,
            "level": 0
        }

    if data_source != "gadm41":
        if gid_1:
            geostore_filter.update({"id1": gid_1})
            boundary_filter.update({"gid_1": gid_1, "level": 1})
        if gid_2:
            geostore_filter.update({"id2": gid_2})
            boundary_filter.update({"gid_2": gid_2, "level": 2})
    else:
        if gid_1:
            geostore_filter.update({"id1": gid_1})
            boundary_filter.update({"gid_1": f"{gid_0}.{gid_1}_1", "level": 1})
        if gid_2:
            geostore_filter.update({"id2": gid_2})
            boundary_filter.update({"gid_2": f"{gid_0}.{gid_1}.{gid_2}_1", "level": 2})


    geostore = Geostore.objects.filter(**geostore_filter)

    should_save = False

    if not geostore.exists():
        should_save = True
        geostore = AdminBoundary.objects.filter(**boundary_filter)

    if not geostore.exists():
        raise NotFound(detail='Geostore not found')

    geostore = geostore.first()

    geom = geostore.geom

    if simplify_thresh:
        geom = geostore.geom.simplify(tolerance=float(simplify_thresh))

    # convert to multipolygon if not
    if geom.geom_type != "MultiPolygon":
        geom = MultiPolygon(geom)

    if should_save:
        geostore_data = {
            "iso": geostore.gid_0,
            "id1": gid_1,
            "id2": gid_2,
            "name_0": geostore.name_0,
            "name_1": geostore.name_1,
            "name_2": geostore.name_2,
            "geom": geom
        }

        geostore = Geostore.objects.create(**geostore_data)

    # geostore_id = geostore.values('id').first()['id']

    return geostore.id



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
class SingleVariableChartSnippet(models.Model):
    CHART_TYPE_CHOICES = [
        ("line",  _("Line Chart")),
        ("column",  _("Vertical Bar Chart")),
        ("bar",  _("Horizontal Bar Chart")),
        ("area",  _("Area Chart")),
        # ("boxplot", "Box Plot"), # TODO: Box plot not implemented in frontend yet
        ("scatter",  _("Scatter Plot")),
        ("warm_stripes",  _("Warming stripes")),
        ("rain_stripes",  _("Rainfall stripes")),
    ]



    title = models.CharField(max_length=255)
    description = RichTextField(features=SUMMARY_RICHTEXT_FEATURES, verbose_name=_('Description'),
                                      help_text=_("Description"), null=True, blank=True)
    dataset = models.ForeignKey(
        "geomanager.RasterFileLayer", on_delete=models.CASCADE, related_name="charts"
    )
    data_unit = models.CharField(max_length=255, blank=True)

    chart_type = models.CharField(max_length=255, choices=CHART_TYPE_CHOICES, default="line")
    chart_color = models.CharField(
        max_length=7,
        default="#0b76e1",
        help_text= _("Hex color code for chart color (e.g., #0b76e1)")
    )

    area_desc = models.TextField(max_length=50,
                                help_text=_("Click on map to generate name"), null=True,  blank=True)
    admin_level = models.IntegerField(choices=ADMIN_LEVEL_CHOICES, default=0, help_text=_("Administrative Level"),  null=True, blank=False )
    
    geom = gis_models.MultiPolygonField(srid=4326, verbose_name=_("Area"), null=True,  blank=True)
    # hidden inputs for determining geostoreid 
    gid0 = models.CharField(null=True, max_length=250, blank = True)
    gid1 = models.CharField(null=True, max_length=250, blank = True)
    gid2 = models.CharField(null=True, max_length=250, blank = True)
    geostore_id = models.UUIDField(default=uuid.uuid4, editable=False)


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
                FieldPanel("gid0", help_text=_("Auto-generated, do not edit"), classname="hidden"),
                FieldPanel("gid1", help_text=_("Auto-generated, do not edit"), classname="hidden"),
                FieldPanel("gid2", help_text=_("Auto-generated, do not edit"), classname="hidden"),
                FieldPanel("area_desc", help_text=_("Click on map to generate name")),
                FieldPanel("geom", widget=BoundaryIDWidget(attrs={"resize_trigger_selector": ".w-tabs__tab.map-resize-trigger"}), help_text=_("Click on map to generate name")),
            ], heading=_("Admin Boundary"))
        ])
    ]

    def __str__(self):
        return f"{self.title} ({self.chart_type} chart) {self.area_desc}"
    

    def save(self, *args, **kwargs):
        self.geostore_id = get_by_admin(self.gid0, self.gid1, self.gid2)
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
        verbose_name =  _("Single-Variable Chart")
        verbose_name_plural =  _("Single-Variable Charts")

    
@register_snippet
class MultiVariableChartSnippet(models.Model):
    
     
    title = models.CharField(max_length=255)
    description = RichTextField(features=SUMMARY_RICHTEXT_FEATURES, verbose_name=_('Description'),
                                        help_text=_("Description"), null=True, blank=True)
    
    multiple_axes = models.BooleanField(default=False, help_text=_("Whether to use multiple axes (one per variable) or a single axis for all variables."))
    variables = StreamField([
        ("chart_variable", ChartVariableBlock())
    ], null=True, blank=True, verbose_name=_("Chart Variables"), min_num=2, help_text=_("Add more variables to display in the chart. Each variable corresponds to a dataset and will be displayed as a separate series in the chart."))


    area_desc = models.TextField(max_length=50,
                                help_text=_("Click on map to generate name"), null=True,  blank=True)
    admin_level = models.IntegerField(choices=ADMIN_LEVEL_CHOICES, default=0, help_text=_("Administrative Level"),  null=True, blank=False )
    
    geom = gis_models.MultiPolygonField(srid=4326, verbose_name=_("Area"), null=True,  blank=True)
    # hidden inputs for determining geostoreid 
    gid0 = models.CharField(null=True, max_length=250, blank = True)
    gid1 = models.CharField(null=True, max_length=250, blank = True)
    gid2 = models.CharField(null=True, max_length=250, blank = True)
    geostore_id = models.UUIDField(default=uuid.uuid4, editable=False)


    panels = [
        TabbedInterface([
        ObjectList([
            FieldPanel("title"),
            FieldPanel("description"),
            FieldPanel("multiple_axes"),
            FieldPanel("variables"),
        ], heading=_("Layer")),
        ObjectList([
                FieldPanel("admin_level"),
                FieldPanel("gid0", help_text=_("Auto-generated, do not edit"), classname="hidden"),
                FieldPanel("gid1", help_text=_("Auto-generated, do not edit"), classname="hidden"),
                FieldPanel("gid2", help_text=_("Auto-generated, do not edit"), classname="hidden"),
                FieldPanel("area_desc", help_text=_("Click on map to generate name")),
                FieldPanel("geom", widget=BoundaryIDWidget(attrs={"resize_trigger_selector": ".w-tabs__tab.map-resize-trigger"}), help_text=_("Click on map to generate name")),
        ], heading=_("Admin Boundary"))
        ])
    ]

    def __str__(self):
        return self.title

    @property
    def multivariable_chart_data(self):
        chart_data = []
        for variable in self.variables:
            var_value = variable.value
            dataset = var_value.get("dataset")
            if dataset:
                chart_data.append({
                    "chart_variable": var_value.get("chart_variable"),
                    "data_unit": var_value.get("data_unit"),
                    "chart_color": var_value.get("chart_color"),
                    "chart_type": var_value.get("chart_type"),
                    "dataset_id": str(dataset.id),
                    "dataset_title": dataset.title,
                    "dataset_dateformat": dataset.date_format,
                })

        
        return json.dumps(chart_data)
    
    class Meta:
        verbose_name =  _("Multi-Variable Chart")
        verbose_name_plural =  _("Multi-Variable Charts")

    def save(self, *args, **kwargs):
        self.geostore_id = get_by_admin(self.gid0, self.gid1, self.gid2)
        super().save(*args, **kwargs)


@register_snippet
class DashboardMap(models.Model):


    title = models.CharField(max_length=255)
    description = RichTextField(features=SUMMARY_RICHTEXT_FEATURES, verbose_name=_('Description'),
                                      help_text=_("Description"), null=True, blank=True)
    area_desc = models.TextField(max_length=50,
                                help_text=_("Click on map to generate name"), null=True,  blank=True)
    admin_level = models.IntegerField(choices=ADMIN_LEVEL_CHOICES, default=0, help_text=_("Administrative Level"), blank=False )
    
    geom = gis_models.MultiPolygonField(srid=4326, verbose_name=_("Area"), null=True,  blank=True)

    map_layer = StreamField([
        ('raster_file_layer', climweb_blocks.UUIDModelChooserBlock(RasterFileLayer, icon="map")),
        ('wms_layer', climweb_blocks.UUIDModelChooserBlock(WmsLayer, icon="map")),
        ('raster_tile_layer', climweb_blocks.UUIDModelChooserBlock(RasterTileLayer, icon="map")),
        ('vector_tile_layer', climweb_blocks.UUIDModelChooserBlock(VectorTileLayer, icon="map")),
    ], null=True, blank=False,verbose_name=_("Map Layers"))


    MAP_TYPE_CHOICES = (
    ("single", _("Single Map")),
    ("comparison", _("Comparison Map")),
    )

    map_type = models.CharField(
        max_length=20,
        choices=MAP_TYPE_CHOICES,
        default="single",
        help_text=_("Select whether this is a single map or a comparison map."),
    )

    # hidden inputs for determining geostoreid 
    gid0 = models.CharField(null=True, max_length=250, blank = True)
    gid1 = models.CharField(null=True, max_length=250, blank = True)
    gid2 = models.CharField(null=True, max_length=250, blank = True)
    geostore_id = models.UUIDField(default=uuid.uuid4, editable=False)

    panels = [
        TabbedInterface([
            ObjectList([
                FieldPanel("title"),
                FieldPanel("description"),
                FieldPanel("map_type"),
                FieldPanel("map_layer"),
            ], heading=_("Layer")),
            ObjectList([
                FieldPanel("admin_level"),
                FieldPanel("area_desc", help_text=_("Click on map to generate name")),
                FieldPanel("gid0", help_text=_("Auto-generated, do not edit"), classname="hidden"),
                FieldPanel("gid1", help_text=_("Auto-generated, do not edit"), classname="hidden"),
                FieldPanel("gid2", help_text=_("Auto-generated, do not edit"), classname="hidden"),
            FieldPanel("geom", widget=BoundaryIDWidget(attrs={"resize_trigger_selector": ".w-tabs__tab.map-resize-trigger"}), help_text=_("Click on map to generate name")),
            ], heading=_("Admin Boundary")),
        ]),
        
    ]

    def clean(self):
        super().clean()

        # Validate the number of map layers based on the map type
        if self.map_type == "single" and len(self.map_layer) > 1 :
            raise ValidationError(_("A single map can only have one map layer."))
        elif self.map_type == "comparison" and len(self.map_layer) != 2:
            raise ValidationError(_("A comparison map must have two map layers."))

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
        """URL for single map or first layer of comparison"""
        if self.map_type == "single":
            return self._generate_mapviewer_url(self.map_layer[0] if self.map_layer else None)
        elif self.map_type == "comparison":
            return self._generate_mapviewer_url(self.map_layer[0] if self.map_layer else None)
        return None

    @property
    def mapviewer_map_url_before(self):
        """URL for the first layer in comparison"""
        if self.map_type == 'comparison' and self.map_layer:
            return self._generate_mapviewer_url(self.map_layer[0])
        return None

    @property 
    def mapviewer_map_url_after(self):
        """URL for the second layer in comparison"""
        if self.map_type == 'comparison' and len(self.map_layer) > 1:
            return self._generate_mapviewer_url(self.map_layer[1])
        return None

    @property
    def mapviewer_comparison_url(self):
        """URL for comparing both layers side by side"""
        if self.map_type == 'comparison' and len(self.map_layer) > 1:
            first_layer = self.map_layer[0].value
            second_layer = self.map_layer[1].value
            
            # Convert UUIDs to strings to avoid JSON serialization errors
            first_dataset_id = str(first_layer.dataset.id) if hasattr(first_layer, 'dataset') and first_layer.dataset else str(first_layer.id)
            second_dataset_id = str(second_layer.dataset.id) if hasattr(second_layer, 'dataset') and second_layer.dataset else str(second_layer.id)
            first_layer_id = str(first_layer.id)
            second_layer_id = str(second_layer.id)
            
            # Create a map config with both datasets
            map_config = {
                "datasets": [
                    {
                        "dataset": "political-boundaries", 
                        "layers": ["political-boundaries"], 
                        "visibility": True
                    },
                    {
                        "dataset": first_dataset_id,
                        "layers": [first_layer_id],
                        "visibility": True,
                        "opacity": 0.8
                    },
                    {
                        "dataset": second_dataset_id,
                        "layers": [second_layer_id],
                        "visibility": True,
                        "opacity": 0.8
                    }
                ],
                "comparison": True
            }

            base_mapviewer_url = reverse("mapview")
            map_str = json.dumps(map_config, separators=(',', ':'))
            map_bytes = map_str.encode()
            map_base64_bytes = base64.b64encode(map_bytes)
            map_byte_str = map_base64_bytes.decode()

            # Use the category from the first layer for menu
            dataset_category_title = "Unknown"
            if hasattr(first_layer, "dataset") and first_layer.dataset and first_layer.dataset.category:
                dataset_category_title = first_layer.dataset.category.title

            menu_config = {"menuSection": "datasets", "datasetCategory": dataset_category_title}
            menu_str = json.dumps(menu_config, separators=(',', ':'))
            menu_bytes = menu_str.encode()
            menu_base64_bytes = base64.b64encode(menu_bytes)
            menu_byte_str = menu_base64_bytes.decode()

            return base_mapviewer_url + f"?map={map_byte_str}&mapMenu={menu_byte_str}&mode=comparison"
        return None

    def _generate_mapviewer_url(self, layer_block):
        """Helper method to generate mapviewer URL for a single layer"""
        if not layer_block:
            return None
            
        base_mapviewer_url = reverse("mapview")
        selected_layer = layer_block.value

        # Create map config with political boundaries and selected layer
        map_config = {
            "datasets": [
                {
                    "dataset": "political-boundaries", 
                    "layers": ["political-boundaries"], 
                    "visibility": True
                }
            ]
        }

        # Add the selected layer to the config
        if hasattr(selected_layer, 'dataset') and selected_layer.dataset:
            # Convert UUIDs to strings to avoid JSON serialization errors
            dataset_id = str(selected_layer.dataset.id)
            layer_id = str(selected_layer.id)
            
            map_config["datasets"].append({
                "dataset": dataset_id,
                "layers": [layer_id],
                "visibility": True
            })

        map_str = json.dumps(map_config, separators=(',', ':'))
        map_bytes = map_str.encode()
        map_base64_bytes = base64.b64encode(map_bytes)
        map_byte_str = map_base64_bytes.decode()

        # Extract dataset category for menu
        dataset_category_title = "Unknown"
        if hasattr(selected_layer, "dataset") and selected_layer.dataset and selected_layer.dataset.category:
            dataset_category_title = selected_layer.dataset.category.title

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

        self.geostore_id = get_by_admin(self.gid0, self.gid1, self.gid2)

        super().save(*args, **kwargs)