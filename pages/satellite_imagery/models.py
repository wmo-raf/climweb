from datetime import datetime

from adminboundarymanager.models import AdminBoundarySettings
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.api.v2.utils import get_full_url
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.contrib.settings.registry import register_setting
from wagtail.fields import StreamField
from wagtail.models import Page

from base.mixins import MetadataPageMixin
from .utils import get_msg_layer_choices, get_msg_layer_details


class MSGLayerBlock(blocks.StructBlock):
    name = blocks.ChoiceBlock(choices=get_msg_layer_choices, label=_("Layer name"))
    label = blocks.CharBlock(max_length=255, required=False, label=_("Layer label"),
                             help_text=_("Leave blank to use default label title from EUMetView"))
    enabled = blocks.BooleanBlock(required=False, default=True, label=_("Enabled"))
    abstract = blocks.TextBlock(required=False, label=_("Layer Abstract"),
                                help_text=_("Leave empty to set from EUMETVIEW Layer details"))
    generate_animation_images = blocks.BooleanBlock(required=False, default=False,
                                                    label=_("Automatically generate animation images"))


@register_setting
class SatelliteImagerySetting(BaseSiteSetting):
    msg_layers = StreamField([("msg_layer", MSGLayerBlock(label="MSG Layer"))],
                             use_json_field=True,
                             blank=True,
                             null=True,
                             block_counts={
                                 'msg_layer': {'max_num': 5},
                             },
                             verbose_name=_("MSG Layers"))

    panels = [
        FieldPanel("msg_layers")
    ]

    @cached_property
    def layers(self):
        layers = []
        for layer in self.msg_layers:
            if layer.value.get("enabled"):
                value = layer.value
                layers.append({
                    "name": value.get("name"),
                    "label": value.get("label"),
                    "abstract": value.get("abstract"),
                    "generate_animation_images": value.get("generate_animation_images")
                })
        return layers

    def save(self, *args, **kwargs):
        for layer in self.msg_layers:
            if not layer.value.get("label") or not layer.value.get("abstract"):
                try:
                    layer_detail = get_msg_layer_details(layer.value.get("name"))
                    if layer_detail:
                        if not layer.value.get("label"):
                            layer.value["label"] = layer_detail.get("title")
                        if not layer.value.get("abstract"):
                            layer.value["abstract"] = layer_detail.get("abstract")
                except Exception:
                    pass
        super().save(*args, **kwargs)


class SatelliteImageryPage(MetadataPageMixin, Page):
    template = "satellite_imagery/satellite_imagery_page.html"
    parent_page_types = ['home.HomePage']
    max_count = 1
    subpage_types = []

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        sat_setting = SatelliteImagerySetting.for_request(request)

        layer_dates_url = reverse("sat_get_layer_time")
        layer_dates_url = get_full_url(request, layer_dates_url)

        layer_images_url = reverse("sat_get_animation_images")
        layer_images_url = get_full_url(request, layer_images_url)

        abm_settings = AdminBoundarySettings.for_request(request)
        abm_extents = abm_settings.combined_countries_bounds
        boundary_tiles_url = get_full_url(request, abm_settings.boundary_tiles_url)

        context.update({
            "layer_dates_url": layer_dates_url,
            "layer_images_url": layer_images_url,
            "eumetview_wms_base_url": "https://view.eumetsat.int/geoserver/wms",
            "msg_layers": sat_setting.layers,
            "bounds": abm_extents,
            "boundary_tiles_url": boundary_tiles_url
        })

        return context


class SatAnimation(ClusterableModel):
    day = models.DateField()
    layer = models.CharField(max_length=255)

    @property
    def layer_slug(self):
        return slugify(self.layer)


def get_upload_to(instance, filename):
    layer_slug = instance.layer_slug
    today = datetime.today().strftime("%Y%m%d")
    return f"satellite-imagery/{today}/{layer_slug}/{filename}"


class SatAnimationImage(models.Model):
    sat_anim = ParentalKey(SatAnimation, related_name='images', on_delete=models.CASCADE)
    date = models.DateTimeField()
    file = models.FileField(upload_to=get_upload_to)

    def __init__(self, *args, layer_slug=None, **kwargs):
        super().__init__(*args, **kwargs)

        if layer_slug:
            self.layer_slug = layer_slug
