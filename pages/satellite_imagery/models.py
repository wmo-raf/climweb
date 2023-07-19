from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page
from adminboundarymanager.models import AdminBoundarySettings

from base.mixins import MetadataPageMixin
from .utils import get_msg_layer_choices, get_msg_layer_title


class MSGLayerBlock(blocks.StructBlock):
    name = blocks.ChoiceBlock(choices=get_msg_layer_choices, label=_("Layer name"))
    label = blocks.CharBlock(max_length=255, required=False, label=_("Layer label"),
                             help_text=_("Leave blank to use default label title from EUMetView"))


class SatelliteImageryPage(MetadataPageMixin, Page):
    template = "satellite_imagery/satellite_imagery_page.html"

    parent_page_types = ["home.HomePage"]
    subpage_types = []
    max_count = 1

    msg_layers = StreamField([("msg_layer", MSGLayerBlock(label=_("MSG Layer")))], use_json_field=True, blank=True,
                             null=True, block_counts={'msg_layer': {'max_num': 5}, }, verbose_name=_("MSG Layers"))

    content_panels = Page.content_panels + [
        FieldPanel("msg_layers")
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        layer_dates_url = reverse("eumetview_get_layer_time")
        layer_dates_url = request.build_absolute_uri(layer_dates_url)
        abm_setting = AdminBoundarySettings.for_request(request)

        context.update({
            "layer_dates_url": layer_dates_url,
            "eumetview_wms_base_url": "https://view.eumetsat.int/geoserver/wms",
            "bounds": abm_setting.combined_countries_bounds,
        })

        return context

    def save_revision(self, *args, **kwargs):
        self.update_msg_layers()
        return super().save_revision(*args, **kwargs)

    def update_msg_layers(self):
        for layer in self.msg_layers:
            if not layer.value.get("label"):
                try:
                    label = get_msg_layer_title(layer.value.get("name"))
                    if label:
                        layer.value["label"] = label
                except Exception:
                    pass

    def save(self, *args, **kwargs):
        self.update_msg_layers()
        return super().save(*args, **kwargs)
