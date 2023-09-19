from datetime import datetime

from capeditor.models import AbstractCapAlertPage
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.models import Page

from base.mixins import MetadataPageMixin
from pages.cap.constants import SEVERITY_MAPPING


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
                "severity": SEVERITY_MAPPING[info.value.get("severity")]
            }

            alert_infos.append(alert_info)

        return alert_infos
