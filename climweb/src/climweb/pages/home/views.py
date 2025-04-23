from adminboundarymanager.models import AdminBoundarySettings
from django.http import JsonResponse
from django.urls import reverse
from geomanager.serializers import RasterFileLayerSerializer
from geomanager.serializers.vector_tile import VectorTileLayerSerializer
from geomanager.serializers.wms import WmsLayerSerializer
from wagtail.api.v2.utils import get_full_url

from climweb.base.models import OrganisationSetting
from .models import HomeMapSettings


def home_map_settings(request):
    config = {
        "zoomLocations": []
    }
    
    abm_settings = AdminBoundarySettings.for_request(request)
    org_settings = OrganisationSetting.for_request(request)
    
    abm_extents = abm_settings.combined_countries_bounds
    boundary_tiles_url = get_full_url(request, abm_settings.boundary_tiles_url)
    
    config.update({
        "bounds": abm_extents,
        "boundaryTilesUrl": boundary_tiles_url,
        "weatherIconsUrl": get_full_url(request, reverse("weather-icons")),
        "forecastSettingsUrl": get_full_url(request, reverse("forecast-settings")),
        "homeMapAlertsUrl": get_full_url(request, reverse("home_map_alerts")),
        "homeForecastDataUrl": get_full_url(request, reverse("home-weather-forecast")),
        "capGeojsonUrl": get_full_url(request, reverse("cap_alerts_geojson")),
    })
    
    if org_settings.country_info:
        config["countryInfo"] = org_settings.country_info
    
    settings = HomeMapSettings.for_request(request)
    
    for location in settings.zoom_locations:
        config["zoomLocations"].append({
            "id": location.id,
            "name": location.value.name,
            "bounds": location.value.bounds,
            "default": location.value.default
        })
    
    if settings.forecast_cluster:
        config["forecastClusterConfig"] = {
            "cluster": True
        }
        
        if settings.forecast_cluster_min_points:
            config["forecastClusterConfig"]["clusterMinPoints"] = settings.forecast_cluster_min_points
        
        if settings.forecast_cluster_radius:
            config["forecastClusterConfig"]["clusterRadius"] = settings.forecast_cluster_radius
    
    config.update({
        "showWarningsLayer": settings.show_warnings_layer,
        "capWarningsLayerDisplayName": settings.warnings_layer_display_name,
        "showLocationForecastLayer": settings.show_location_forecast_layer,
        "locationForecastLayerDisplayName": settings.location_forecast_layer_display_name,
        "locationForecastDateDisplayFormat": settings.location_forecat_date_display_format,
    })
    
    dynamic_map_layers = []
    for index, block in enumerate(settings.map_layers):
        LayerSerializer = None
        if block.block_type == "raster_file_layer":
            LayerSerializer = RasterFileLayerSerializer
        elif block.block_type == "wms_layer":
            LayerSerializer = WmsLayerSerializer
        elif block.block_type == "vector_tile_layer":
            LayerSerializer = VectorTileLayerSerializer
        
        if LayerSerializer:
            layer = block.value.get("layer")
            layer_config = LayerSerializer(layer, context={"request": request}).data
            
            layer_config.update({
                "icon": block.value.get("icon"),
                "display_name": block.value.get("display_name"),
                "position": index,
                "show_by_default": block.value.get("default"),
            })
            
            dynamic_map_layers.append(layer_config)
    
    config["dynamicMapLayers"] = dynamic_map_layers
    
    return JsonResponse(config)
