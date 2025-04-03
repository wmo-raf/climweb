from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from geomanager.models import SubCategory, Metadata

from wagtail.admin.panels import FieldPanel
from wagtail.api.v2.utils import get_full_url
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.contrib.settings.registry import register_setting


@register_setting(name="cap-mapviewer-settings")
class CAPGeomanagerSettings(BaseSiteSetting):
    show_on_mapviewer = models.BooleanField(default=True, verbose_name=_("Show on MapViewer"),
                                            help_text=_("Check to show cap alerts on MapViewer"))
    layer_title = models.CharField(max_length=100, blank=True, null=True, default="Weather Alerts",
                                   verbose_name=_("CAP Alerts Layer Title"))
    geomanager_subcategory = models.ForeignKey(SubCategory, null=True, blank=True,
                                               verbose_name=_("CAP Alerts Layer SubCategory"),
                                               on_delete=models.SET_NULL)
    geomanager_layer_metadata = models.ForeignKey(Metadata, on_delete=models.SET_NULL, blank=True, null=True,
                                                  verbose_name=_("CAP Layer Metadata"))
    auto_refresh_interval = models.IntegerField(blank=True, null=True,
                                                verbose_name=_("Auto Refresh interval in minutes"),
                                                help_text=_(
                                                    "Refresh cap alerts on the map after this minutes. Leave blank "
                                                    "to disable auto refreshing"))
    
    panels = [
        FieldPanel("show_on_mapviewer"),
        FieldPanel("layer_title"),
        FieldPanel("geomanager_subcategory"),
        FieldPanel("geomanager_layer_metadata"),
        FieldPanel("auto_refresh_interval"),
    ]
    
    @staticmethod
    def get_cap_geojson_url(request=None):
        geojson_url = reverse("cap_alerts_geojson")
        
        if request:
            geojson_url = get_full_url(request, geojson_url)
        
        return geojson_url
