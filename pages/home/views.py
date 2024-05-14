from adminboundarymanager.models import AdminBoundarySettings
from django.http import JsonResponse
from django.urls import reverse
from wagtail.api.v2.utils import get_full_url
from django.shortcuts import render

from base.models import OrganisationSetting
from pages.home.models import HomeMapSettings
from climweb_wdqms.models import Station,Transmission
from django.db.models.functions import TruncMonth
from django.db.models import Max

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
        "forecastDataApiUrl": get_full_url(request, reverse("forecast-list")),
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

    return JsonResponse(config)


def wdqms_reports(request):

    stations = Station.objects.all()
    transmissions = Transmission.objects.all()
    variables = transmissions.values_list('variable', flat=True).distinct()
    years = transmissions.values_list('received_date__year', flat=True).distinct()
    latest_date = transmissions.filter(variable=variables[0]).order_by('received_date').values_list('received_date__date',  flat=True).last()

    abm_settings = AdminBoundarySettings.for_request(request)
    org_settings = OrganisationSetting.for_request(request)

    abm_extents = abm_settings.combined_countries_bounds
    boundary_tiles_url = get_full_url(request, abm_settings.boundary_tiles_url)
  

    return render(request, "home/wdqms_report/report_index.html", {
        'stations':stations,
        'variables':variables,
        'latest_date':latest_date,
        'years':years,
        'bounds':abm_extents,
        'boundary_tiles_url':boundary_tiles_url
    })