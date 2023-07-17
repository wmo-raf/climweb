from django.http import JsonResponse

from .utils import get_layer_time


def eumetsat_get_layer_time_values(request):
    layer = request.GET.get("layer", None)
    time_values = []

    if layer:
        time_values = get_layer_time(layer)

    return JsonResponse(time_values, safe=False)
