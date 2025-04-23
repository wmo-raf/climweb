import json

from alertwise.capeditor.blocks import BoundaryFieldBlock, PolygonOrMultiPolygonFieldBlock
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from shapely.geometry import shape
from wagtail import blocks
from wagtail.blocks import StructValue


class AreaBoundaryStructValue(StructValue):
    @cached_property
    def geojson(self):
        polygon = self.get("boundary")
        return json.loads(polygon)
    
    @cached_property
    def bounds(self):
        geojson = self.geojson
        geo = shape(geojson)
        return geo.bounds
    
    @cached_property
    def name(self):
        return self.get("areaDesc")
    
    @cached_property
    def default(self):
        return self.get("default")


class AreaPolygonStructValue(StructValue):
    
    @cached_property
    def geojson(self):
        polygon = self.get("polygon")
        return json.loads(polygon)
    
    @cached_property
    def bounds(self):
        geojson = self.geojson
        geo = shape(geojson)
        return geo.bounds
    
    @cached_property
    def name(self):
        return self.get("areaDesc")
    
    @cached_property
    def default(self):
        return self.get("default")


class AreaBoundaryBlock(blocks.StructBlock):
    class Meta:
        value_class = AreaBoundaryStructValue
    
    ADMIN_LEVEL_CHOICES = (
        (0, _("Level 0")),
        (1, _("Level 1")),
        (2, _("Level 2")),
        (3, _("Level 3"))
    )
    
    areaDesc = blocks.TextBlock(label=_("Area/Region Name"))
    default = blocks.BooleanBlock(label=_("Default"), required=False)
    admin_level = blocks.ChoiceBlock(choices=ADMIN_LEVEL_CHOICES, default=1, label=_("Administrative Level"))
    boundary = BoundaryFieldBlock(label=_("Boundary"), help_text=_("Click to select boundary on the map"))


class AreaPolygonBlock(blocks.StructBlock):
    class Meta:
        value_class = AreaPolygonStructValue
    
    areaDesc = blocks.TextBlock(label=_("Area/Region Name"))
    default = blocks.BooleanBlock(label=_("Default"), required=False)
    polygon = PolygonOrMultiPolygonFieldBlock(label=_("Polygon"), help_text=_("Draw custom area on the map"))
