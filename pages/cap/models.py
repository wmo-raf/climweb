from capeditor.models import AbstractCapAlertPage
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from wagtail.models import Page

from base.mixins import MetadataPageMixin
from pages.cap.constants import SEVERITY_MAPPING


class CapAlertPage(MetadataPageMixin, AbstractCapAlertPage):
    template = "cap/alert_detail.html"

    parent_page_types = ["home.HomePage"]
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

            if timezone.now() > start_time:
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
