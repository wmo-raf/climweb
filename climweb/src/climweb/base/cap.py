import json

from django.utils.translation import gettext as _

from climweb.base.models import ImportantPages

DEFAULT_STYLE = {
    'version': 8,
    'sources': {
        'carto-dark': {
            'type': 'raster',
            'tiles': [
                "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
                "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
                "https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
                "https://d.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"
            ]
        },
        'carto-light': {
            'type': 'raster',
            'tiles': [
                "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
                "https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
                "https://c.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
                "https://d.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png"
            ]
        },
        'wikimedia': {
            'type': 'raster',
            'tiles': [
                "https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png"
            ]
        }
    },
    'layers': [{
        'id': 'carto-light-layer',
        'source': 'carto-light',
        'type': 'raster',
        'minzoom': 0,
        'maxzoom': 22
    }]
}

CAP_LAYERS = [
    {
        "type": "fill",
        "paint": {
            "fill-color": [
                "match",
                ["get", "severity"],
                "Extreme",
                "#d72f2a",
                "Severe",
                "#fe9900",
                "Moderate",
                "#ffff00",
                "Minor",
                "#03ffff",
                "#3366ff",
            ],
            "fill-opacity": 1,
        },
        "filter": [
            "in",
            ["get", "severity"],
            ["literal", ["Extreme", "Severe", "Moderate", "Minor"]],
        ],
    },
    {
        "type": "line",
        "paint": {
            "line-color": [
                "match",
                ["get", "severity"],
                "Extreme",
                "#ac2420",
                "Severe",
                "#ca7a00",
                "Moderate",
                "#cbcb00",
                "Minor",
                "#00cdcd",
                "#003df4",
            ],
            "line-width": 0.1,
        },
        "filter": [
            "in",
            ["get", "severity"],
            ["literal", ["Extreme", "Severe", "Moderate", "Minor"]],
        ],
    },
]


def create_cap_geomanager_dataset(cap_geomanager_settings, has_live_alerts, request=None):
    sub_category = cap_geomanager_settings.geomanager_subcategory
    
    more_info = None
    
    if request:
        important_pages = ImportantPages.for_request(request)
        if important_pages.cap_warnings_list_page:
            more_info = {
                "linkText": _("Go to warnings list"),
                "linkUrl": important_pages.cap_warnings_list_page.get_full_url(request),
                "isButton": True,
                "showArrow": True
            }
    
    if not sub_category:
        return None
    
    title = cap_geomanager_settings.layer_title
    metadata = cap_geomanager_settings.geomanager_layer_metadata
    auto_refresh_interval = cap_geomanager_settings.auto_refresh_interval
    
    # convert to milliseconds
    if auto_refresh_interval:
        auto_refresh_interval = auto_refresh_interval * 60 * 1000
    
    cap_geojson_url = cap_geomanager_settings.get_cap_geojson_url(request)
    
    dataset_id = "cap_alerts"
    
    dataset = {
        "id": dataset_id,
        "dataset": dataset_id,
        "name": title,
        "isCapAlert": True,
        "capConfig": {
            "baseUrl": cap_geojson_url,
            "refreshInterval": auto_refresh_interval
        },
        "initialVisible": has_live_alerts,
        "layer": dataset_id,
        "category": sub_category.category.pk,
        "sub_category": sub_category.pk,
        "public": True,
        "layers": []
    }
    
    if metadata:
        dataset.update({"metadata": metadata.pk})
    
    layer = {
        "id": dataset_id,
        "dataset": dataset_id,
        "name": title,
        "layerConfig": {
            "type": "vector",
            "source": {
                "type": "geojson",
                "data": {"type": "FeatureCollection", "features": []},
            },
            "render": {
                "layers": CAP_LAYERS
            },
        },
        "layerFilterParams": {
            "severity": [
                {"label": "Extreme", "value": "Extreme"},
                {"label": "Severe", "value": "Severe"},
                {"label": "Moderate", "value": "Moderate"},
                {"label": "Minor", "value": "Minor"},
            ],
        },
        "layerFilterParamsConfig": [
            {
                "isMulti": True,
                "type": "checkbox",
                "key": "severity",
                "required": "true",
                "default": [
                    {"label": "Extreme", "value": "Extreme"},
                    {"label": "Severe", "value": "Severe"},
                    {"label": "Moderate", "value": "Moderate"},
                ],
                "sentence": "Filter by Severity {selector}",
                "options": [
                    {"label": "Extreme", "value": "Extreme"},
                    {"label": "Severe", "value": "Severe"},
                    {"label": "Moderate", "value": "Moderate"},
                    {"label": "Minor", "value": "Minor"},
                    {"label": "Unknown", "value": "Unknown"},
                ],
            },
        ],
        "legendConfig": {
            "items": [
                {
                    "color": "#d72f2a",
                    "name": "Extreme Severity",
                },
                {
                    "color": "#fe9900",
                    "name": "Severe Severity",
                },
                {
                    "color": "#ffff00",
                    "name": "Moderate Severity",
                },
                {
                    "color": "#03ffff",
                    "name": "Minor Severity",
                },
                {
                    "color": "#3366ff",
                    "name": "Unknown Severity",
                },
            ],
            "type": "basic",
        },
        "interactionConfig": {
            "capAlert": True,
            "type": "intersection",
        },
    }
    
    if more_info:
        layer["moreInfo"] = more_info
    
    dataset["layers"].append(layer)
    
    return dataset


def get_cap_map_style(geojson):
    style = DEFAULT_STYLE
    style["sources"].update({"cap_alert": {"type": "geojson", "data": geojson}})
    layers = CAP_LAYERS
    for layer in layers:
        layer_type = layer.get("type")
        layer["source"] = "cap_alert"
        
        if layer_type == "fill":
            layer["id"] = "cap_alert_fill"
        
        if layer_type == "line":
            layer["id"] = "cap_alert_line"
        
        if layer.get("filter"):
            del layer["filter"]
    
    style["layers"].extend(layers)

    return style


def extract_polygon_geometry(geojson):
    """
    Return the first Polygon/MultiPolygon geometry found in a GeoJSON geometry,
    Feature or FeatureCollection, or None if none is found.
    """
    if not isinstance(geojson, dict):
        return None

    geojson_type = geojson.get("type")

    if geojson_type == "FeatureCollection":
        for feature in geojson.get("features") or []:
            geometry = extract_polygon_geometry(feature)
            if geometry is not None:
                return geometry
        return None

    if geojson_type == "Feature":
        return extract_polygon_geometry(geojson.get("geometry"))

    if geojson_type in ("Polygon", "MultiPolygon"):
        return geojson

    return None


def build_area_info_blocks(request):
    """
    Build the ``info`` StreamField raw value with a single Alert Information block
    whose area is pre-filled from the ``geometry`` parameter, or None if no valid
    Polygon/MultiPolygon geometry is provided.

    The geometry is read from POST (the MapViewer submits it as a form body to
    avoid GET URL length limits) with a GET fallback for manual testing.
    """
    data = request.POST if request.method == "POST" else request.GET

    geometry_param = data.get("geometry")
    if not geometry_param:
        return None

    try:
        geojson = json.loads(geometry_param)
    except (ValueError, TypeError):
        return None

    geometry = extract_polygon_geometry(geojson)
    if geometry is None:
        return None

    area_desc = (data.get("areaDesc") or "").strip()

    return [
        {
            "type": "alert_info",
            "value": {
                "area": [
                    {
                        "type": "polygon_block",
                        "value": {
                            "areaDesc": area_desc,
                            "polygon": json.dumps(geometry),
                        },
                    }
                ],
            },
        }
    ]
