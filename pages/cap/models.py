from capeditor.models import AbstractCapAlertPage
from capeditor.pubsub.publish import publish_cap_mqtt_message
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from geomanager.models import SubCategory, Metadata
from wagtail.admin.panels import FieldPanel
from wagtail.api.v2.utils import get_full_url
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.contrib.settings.registry import register_setting
from wagtail.models import Page
from wagtail.signals import page_published

from base.mixins import MetadataPageMixin
from pages.cap.tasks import generate_cap_alert_card


class CapAlertListPage(MetadataPageMixin, Page):
    template = "cap/alert_list.html"
    parent_page_types = ["home.HomePage"]
    subpage_types = ["cap.CapAlertPage"]
    max_count = 1

    heading = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("CAP Alerts Heading"))

    content_panels = Page.content_panels + [
        FieldPanel("heading"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        cap_rss_feed_url = get_full_url(request, reverse("cap_alert_feed"))

        context.update({
            "cap_rss_feed_url": cap_rss_feed_url,
        })

        return context

    @cached_property
    def cap_alerts(self):
        alerts = CapAlertPage.objects.all().live().filter(status="Actual").order_by('-sent')
        alert_infos = []

        for alert in alerts:
            for alert_info in alert.infos:
                alert_infos.append(alert_info)

        alert_infos = sorted(alert_infos, key=lambda x: x.get("sent", {}), reverse=True)

        return alert_infos

    @cached_property
    def alerts_by_expiry(self):
        all_alerts = self.cap_alerts
        active_alerts = []
        past_alerts = []

        for alert in all_alerts:
            if alert.get("expired"):
                past_alerts.append(alert)
            else:
                active_alerts.append(alert)

        return {
            "active_alerts": active_alerts,
            "past_alerts": past_alerts
        }

    @cached_property
    def filters(self):
        alerts = self.cap_alerts

        filters = {
            "severity": {},
            "event_types": {}
        }

        for alert_info in alerts:
            severity = alert_info.get("severity")
            severity_val = severity.get("severity")

            event_type = alert_info.get("info", {}).value.get('event')

            if filters["event_types"].get(event_type):
                count = filters["event_types"].get(event_type).get("count") + 1
                filters["event_types"].get(event_type).update({"count": count})
            else:
                filters["event_types"].update({event_type: {
                    "count": 1,
                    "label": event_type
                }})

            if filters["severity"].get(severity_val):
                count = filters["severity"].get(severity_val).get("count") + 1
                filters["severity"].get(severity_val).update({"count": count})
            else:
                filters["severity"].update({severity_val: {
                    "count": 1,
                    "label": severity.get("label")
                }})

        return filters


class CapAlertPage(MetadataPageMixin, AbstractCapAlertPage):
    template = "cap/alert_detail.html"

    parent_page_types = ["cap.CapAlertListPage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        *AbstractCapAlertPage.content_panels
    ]

    class Meta:
        ordering = ["-sent"]

    @cached_property
    def xml_link(self):
        return reverse("cap_alert_detail", args=(self.identifier,))

    @cached_property
    def infos(self):
        infos = super().infos

        # order by severity
        infos = sorted(infos, key=lambda x: x.get("severity", {}).get("id"), reverse=True)

        return infos

    def get_geojson_features(self, request=None):
        features = []

        for info_item in self.infos:
            info = info_item.get("info")
            if info.value.geojson:
                web = info_item.get("url")
                if request:
                    web = get_full_url(request, web)

                properties = {
                    "id": self.identifier,
                    "event": info_item.get("event"),
                    "headline": info.value.get("headline"),
                    "severity": info.value.get("severity"),
                    "urgency": info.value.get("urgency"),
                    "certainty": info.value.get("certainty"),
                    "severity_color": info_item.get("severity", {}).get("color"),
                    "sent": self.sent,
                    "onset": info.value.get("onset"),
                    "expires": info.value.get("expires"),
                    "web": web,
                    "description": info.value.get("description"),
                    "instruction": info.value.get("instruction")
                }

                info_features = info.value.features
                for feature in info_features:
                    feature["properties"].update(**properties)
                    feature["order"] = info_item.get("severity", {}).get("id", 0)
                    features.append(feature)

        features = sorted(features, key=lambda x: x.get("order"))
        return features


@register_setting(name="cap-geomanager-settings")
class CAPGeomanagerSettings(BaseSiteSetting):
    show_on_mapviewer = models.BooleanField(default=False, verbose_name=_("Show on MapViewer"),
                                            help_text=_("Check to show cap alerts on MapViewer"))
    layer_title = models.CharField(max_length=100, blank=True, null=True, default="Weather Alerts",
                                   verbose_name=_("CAP Alerts Layer Title"))
    geomanager_subcategory = models.ForeignKey(SubCategory, null=True, blank=True,
                                               verbose_name=_("Stations Layer SubCategory"),
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


def on_publish_cap_alert(sender, **kwargs):
    instance = kwargs['instance']
    try:
        # publish cap alert to mqtt
        topic = "cap/alerts/all"
        publish_cap_mqtt_message(instance, topic)
    except Exception as e:
        pass

    generate_cap_alert_card(instance.id)


page_published.connect(on_publish_cap_alert, sender=CapAlertPage)
