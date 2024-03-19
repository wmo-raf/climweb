from django.http import JsonResponse

from pages.home.models import HomeMapSettings


def home_map_settings(request):
    config = {
        "zoom_locations": []
    }

    settings = HomeMapSettings.for_request(request)

    for location in settings.zoom_locations:
        config["zoom_locations"].append({
            "name": location.value.name,
            "bounds": location.value.bounds,
            "default": location.value.default
        })

    return JsonResponse(config)
