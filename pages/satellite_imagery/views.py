from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone

from .models import SatAnimation
from .utils import get_layer_time, get_anim_upload_path


def eumetsat_get_layer_time_values(request):
    layer = request.GET.get("layer", None)
    time_values = []

    if layer:
        time_values = get_layer_time(layer)

    return JsonResponse(time_values, safe=False)


def get_today_layer_animation_images(request):
    layer = request.GET.get("layer", None)
    date_format = "%Y-%m-%dT%H:%M:%S.%fZ"

    response = {}

    if layer:
        today = timezone.datetime.today()
        sat_anim, created = SatAnimation.objects.get_or_create(day=today, layer=layer)

        media_url = settings.MEDIA_URL

        upload_path = get_anim_upload_path(sat_anim)

        upload_path = request.build_absolute_uri(media_url + upload_path)

        response.update({"upload_path": upload_path})

        sat_anim_images = sat_anim.images.all().order_by("date")

        images_dates = []
        for image in sat_anim_images:
            images_dates.append(image.date.strftime(date_format))

        response.update({"dates": images_dates})

    return JsonResponse(response)
