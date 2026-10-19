from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from climweb.pages.home.models import HomeMapSettings
from climweb.pages.home.views import get_map_config
from .models import ServicePage


def service_map_settings(request, page_id):
    page = get_object_or_404(ServicePage.objects.live(), pk=page_id)

    # Layers come from the page; boundaries, basemaps and the warnings layer follow the home map settings.
    # City forecasts are left to the home page.
    config = get_map_config(
        request,
        HomeMapSettings.for_request(request),
        page.map_layers,
        show_location_forecast=False,
    )

    return JsonResponse(config)
