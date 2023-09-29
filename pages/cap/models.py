import os.path
from datetime import datetime

from adminboundarymanager.models import AdminBoundarySettings
from capeditor.models import AbstractCapAlertPage
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.images.models import Image
from wagtail.models import Page, Site
from wagtail.signals import page_published

from base.mixins import MetadataPageMixin
from base.models import OrganisationSetting
from pages.cap.constants import SEVERITY_MAPPING, URGENCY_MAPPING, CERTAINTY_MAPPING
from pages.cap.utils import cap_geojson_to_image, generate_cap_summary_image


class CapAlertListPage(MetadataPageMixin, Page):
    template = "cap/alert_list.html"
    parent_page_types = ["home.HomePage"]
    subpage_types = ["cap.CapAlertPage"]
    max_count = 1

    heading = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("CAP Alerts Heading"))

    content_panels = Page.content_panels + [
        FieldPanel("heading"),
    ]

    @cached_property
    def cap_alerts(self):
        alerts = CapAlertPage.objects.all().live().order_by('-sent')
        active_alert_infos = []

        for alert in alerts:
            for alert_info in alert.infos:
                info = alert_info.get("info")
                if info.value.get('expires').date() >= datetime.today().date():
                    active_alert_infos.append(alert_info)

        return active_alert_infos

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

    @cached_property
    def xml_link(self):
        return reverse("cap_alert_detail", args=(self.identifier,))

    @cached_property
    def infos(self):
        alert_infos = []
        for info in self.info:
            start_time = info.value.get("effective") or self.sent

            if info.value.get('expires').date() < datetime.today().date():
                status = "Expired"
            elif timezone.now() > start_time:
                status = "Ongoing"
            else:
                status = "Expected"

            area_desc = [area.get("areaDesc") for area in info.value.area]
            area_desc = ",".join(area_desc)

            alert_info = {
                "info": info,
                "status": status,
                "url": self.url,
                "event": f"{info.value.get('event')} ({area_desc})",
                "event_icon": info.value.event_icon,
                "severity": SEVERITY_MAPPING[info.value.get("severity")],
                "utc": start_time,
                "urgency": URGENCY_MAPPING[info.value.get("urgency")],
                "certainty": CERTAINTY_MAPPING[info.value.get("certainty")],
                "effective": start_time,
                "expires": info.value.get('expires'),
            }

            alert_infos.append(alert_info)

        return alert_infos

    def get_geojson_features(self, request=None):
        features = []

        for info_item in self.infos:
            info = info_item.get("info")
            if info.value.geojson:
                web = info_item.get("url")
                if request:
                    web = request.build_absolute_uri(web)

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
                    features.append(feature)

        return features

    def generate_geojson_map_image(self):
        site = Site.objects.get(is_default_site=True)

        abm_settings = AdminBoundarySettings.for_site(site)
        org_settings = OrganisationSetting.for_site(site)
        abm_extents = abm_settings.combined_countries_bounds

        features = self.get_geojson_features()
        if features:
            feature_coll = {
                "type": "FeatureCollection",
                "features": features,
            }

            if abm_extents:
                # format to what matplotlib expects
                abm_extents = [abm_extents[0], abm_extents[2], abm_extents[1], abm_extents[3]]

            cap_detail = {
                "title": self.title,
                "org_name": org_settings.name,
            }
            org_logo = org_settings.logo
            if org_logo:
                cap_detail.update({
                    "org_logo_file": os.path.join(settings.MEDIA_ROOT, org_logo.file.path)
                })

            img_buffer = cap_geojson_to_image(feature_coll, abm_extents)
            file = generate_cap_summary_image(img_buffer, cap_detail, f"{self.identifier}.png")
            # file = ContentFile(img_buffer.getvalue(), f"{self.identifier}.png")

            if self.search_image:
                self.search_image.delete()

            self.search_image = Image(title=self.title)
            self.search_image.file = file
            self.search_image.save()

            self.save()


def on_publish_cap_alert(sender, **kwargs):
    instance = kwargs['instance']
    instance.generate_geojson_map_image()


page_published.connect(on_publish_cap_alert, sender=CapAlertPage)
