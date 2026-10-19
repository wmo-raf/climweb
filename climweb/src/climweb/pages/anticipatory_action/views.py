from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from wagtail.api.v2.utils import get_full_url

from climweb.pages.home.models import HomeMapSettings
from climweb.pages.home.views import get_map_config
from .cap import get_alerts_geojson, is_cap_installed
from .models import AnticipatoryActionPage


def get_live_page(page_id):
    return get_object_or_404(AnticipatoryActionPage.objects.live(), pk=page_id)


def anticipatory_action_map_settings(request, page_id):
    page = get_live_page(page_id)
    
    cap_geojson_url = None
    if is_cap_installed():
        cap_geojson_url = get_full_url(request, reverse("anticipatory-action-cap-geojson", args=[page.pk]))
    
    config = get_map_config(
        request,
        HomeMapSettings.for_request(request),
        page.map_layers,
        show_location_forecast=False,
        cap_geojson_url=cap_geojson_url,
    )
    
    config["showWarningsLayer"] = is_cap_installed() and page.show_cap_alerts
    
    return JsonResponse(config)


def anticipatory_action_cap_geojson(request, page_id):
    page = get_live_page(page_id)
    return JsonResponse(get_alerts_geojson(page.active_cap_alerts, request))

