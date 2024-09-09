import logging
from datetime import timedelta

import pytz
from adminboundarymanager.models import AdminBoundarySettings
from celery.signals import worker_ready
from celery_singleton import Singleton, clear_locks
from climweb.config.celery import app
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.text import slugify
from wagtail.models import Site

from .models import (
    SatelliteImagerySetting,
    SatAnimation,
    SatAnimationImage
)
from .utils import get_layer_time, get_wms_map

logger = logging.getLogger(__name__)


@app.task(
    base=Singleton,
    bind=True
)
def download_imagery():
    today = timezone.datetime.today()

    date_format = "%Y-%m-%dT%H:%M:%S.%fZ"

    site = Site.objects.get(is_default_site=True)
    sat_setting = SatelliteImagerySetting.for_site(site)

    abm_settings = AdminBoundarySettings.for_site(site)
    abm_extents = abm_settings.combined_countries_bounds

    if abm_extents:
        # format to what matplotlib expects
        abm_extents = [abm_extents[0], abm_extents[2], abm_extents[1], abm_extents[3]]

    msg_layers = sat_setting.layers

    for layer in msg_layers:
        if layer.get("generate_animation_images"):
            layer_name = layer.get("name")

            print(f"Processing layer {layer_name}")

            # Delete old animations
            SatAnimation.objects.filter(day__lt=today).delete()

            # get sat anim instance for today
            sat_anim, created = SatAnimation.objects.get_or_create(day=today, layer=layer_name)

            time_values = get_layer_time(layer_name, as_timestamp=False)

            for time_obj in time_values:
                utc = time_obj.replace(tzinfo=pytz.UTC)
                local_time = utc.astimezone(timezone.get_current_timezone())

                if local_time.date() == today.date():
                    time_str = time_obj.strftime(date_format)

                    exists = sat_anim.images.filter(date=time_str).exists()

                    if not exists:
                        print(f"Generating image for time  '{time_str}' and layer '{layer_name}'")

                        try:
                            img_buffer = get_wms_map(layer_name, time_str, abm_extents)

                            img = SatAnimationImage(date=time_str, layer_slug=slugify(layer_name))
                            img.file = ContentFile(img_buffer.getvalue(), f"{time_str}.png")
                            sat_anim.images.add(img)
                            sat_anim.save()
                        except Exception as e:
                            print(e)
                            pass


@worker_ready.connect
def unlock_all(**kwargs):
    clear_locks(app)


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        timedelta(minutes=15),
        download_imagery.s(),
        name="process-satellite-imagery-every-15-minutes",
    )
