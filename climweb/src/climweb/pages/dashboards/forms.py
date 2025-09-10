from django.contrib.gis.forms import BaseGeometryWidget
from django.forms import Widget, Media
from django.urls import reverse
from wagtail.telepath import register
from wagtail.widget_adapters import WidgetAdapter
from django.contrib.gis.forms import GeometryField as BaseGeometryField
from django.contrib.gis.geometry import json_regex

class BaseMapWidget(Widget):
    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        boundary_info_url = reverse("admin_boundary_info")
        context.update({
            "boundary_info_url": boundary_info_url
        })
        
        return context
    
class BasePolygonWidget(BaseGeometryWidget, BaseMapWidget):
    def serialize(self, value):
        return value.json if value else ""
    
    def deserialize(self, value):
        value = value.strip()
        if value:
            return super().deserialize(value)
        return None


class BoundaryIDWidget(BasePolygonWidget, BaseMapWidget):
    template_name = "widgets/boundary_polygon_widget.html"
    map_srid = 4326
    
    def __init__(self, attrs=None):
        default_attrs = {
            "class": "dashboards-widget__boundary-input",
        }
        attrs = attrs or {}
        attrs = {**default_attrs, **attrs}
        
        super().__init__(attrs=attrs)

    def serialize(self, value):
        return value.json if value else ""
    
    def deserialize(self, value):
        geom = super().deserialize(value)
        # GeoJSON assumes WGS84 (4326). Use the map's SRID instead.
        if geom and json_regex.match(value) and self.map_srid != 4326:
            geom.srid = self.map_srid
        return geom
    
    @property
    def media(self):
        css = {
            "all": [
                "css/widget/boundary-widget.css",
                "css/maplibre-gl.css",
            ]
        }
        
        js = [
            "js/maplibre-gl.js",
            "js/turf.min.js",
            "js/widget/boundary-polygon-widget.js",
        ]
        
        return Media(js=js, css=css)


class MultiPolygonGeometryField(BaseGeometryField):
    geom_type = 'MULTIPOLYGON'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget.geom_type = self.geom_type

class BoundaryMultiPolygonField(MultiPolygonGeometryField):
    widget = BoundaryIDWidget
