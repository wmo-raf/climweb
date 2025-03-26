from adminboundarymanager.models import AdminBoundarySettings
from django.http import JsonResponse
from django.urls import reverse
from geomanager.serializers import RasterFileLayerSerializer
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
        "showLocationForecastLayer": settings.show_location_forecast_layer,
        "locationForecastDateDisplayFormat": settings.location_forecat_date_display_format,
    })
    
    dynamic_map_layers = []
    for index, block in enumerate(settings.map_layers):
        if block.block_type == "raster_layer":
            raster_layer = block.value.get("layer")
            layer_config = RasterFileLayerSerializer(raster_layer, context={"request": request}).data
            
            layer_config.update({
                "icon": block.value.get("icon"),
                "display_name": block.value.get("display_name"),
                "position": index
            })
            
            dynamic_map_layers.append(layer_config)
    
    config["dynamicMapLayers"] = dynamic_map_layers
    
    return JsonResponse(config)
