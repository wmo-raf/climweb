import json
from typing import List

from capeditor.constants import SEVERITY_MAPPING
from capeditor.models import CapSetting
from capeditor.renderers import CapXMLRenderer
from capeditor.serializers import AlertSerializer
from django.contrib.syndication.views import Feed
from django.core.validators import validate_email
from django.db.models.base import Model
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.feedgenerator import Enclosure, rfc2822_date
from django.utils.feedgenerator import Rss201rev2Feed
from rest_framework import generics
from wagtail.models import Site

from .models import CapAlertPage


class CustomFeed(Rss201rev2Feed):
    content_type = 'application/xml'

    def add_root_elements(self, handler):
        super().add_root_elements(handler)
        pubDate = rfc2822_date(self.latest_post_date())
        handler.addQuickElement('pubDate', pubDate)


class AlertListFeed(Feed):
    feed_copyright = "public domain"
    language = "en"

    feed_type = CustomFeed

    @staticmethod
    def link():
        return reverse("cap_alert_feed")

    def title(self):
        try:
            site = Site.objects.get(is_default_site=True)
            if site:
                cap_setting = CapSetting.for_site(site)
                return f"Latest Official Public alerts from {cap_setting.sender_name}"

        except Exception:
            pass

        else:
            return "Latest Official Public alerts"

        return None

    def description(self):

        try:
            site = Site.objects.get(is_default_site=True)
            if site:
                cap_setting = CapSetting.for_site(site)
                return f"This feed lists the most recent Official Public alerts from {cap_setting.sender_name}"

        except Exception:
            pass

        else:
            return "This feed lists the most recent Official Public alerts"

        return None

    def items(self):
        alerts = CapAlertPage.objects.all().live().filter(status="Actual")
        return alerts

    def item_title(self, item):
        return item.title

    def item_link(self, item):
        return reverse("cap_alert_xml", args=[item.identifier])

    def item_description(self, item):
        return item.info[0].value.get('description')

    def item_pubdate(self, item):
        return item.sent

    def item_enclosures(self, item: Model) -> List[Enclosure]:
        return super().item_enclosures(item)

    def item_guid(self, item):
        return item.identifier

    def item_author_name(self, item):
        try:
            site = Site.objects.get(is_default_site=True)
            if site:
                cap_setting = CapSetting.for_site(site)
                if cap_setting.sender_name:
                    return cap_setting.sender_name
        except Exception:
            pass

        return None

    def item_author_email(self, item):
        try:
            site = Site.objects.get(is_default_site=True)
            if site:
                cap_setting = CapSetting.for_site(site)
                if cap_setting.sender:
                    # validate if sender is email address
                    validate_email(cap_setting.sender)
                    return cap_setting.sender
        except Exception:
            pass

        return None

    def item_categories(self, item):
        return [item.info[0].value.get('category')]


class AlertDetail(generics.RetrieveAPIView):
    serializer_class = AlertSerializer
    serializer_class.Meta.model = CapAlertPage

    renderer_classes = (CapXMLRenderer,)
    queryset = CapAlertPage.objects.live().filter(status="Actual")

    lookup_field = "identifier"


def cap_geojson(request):
    alerts = CapAlertPage.objects.all().live().filter(status="Actual")
    active_alert_infos = []

    for alert in alerts:
        for info in alert.info:
            if info.value.get('expires') > timezone.localtime():
                active_alert_infos.append(alert.id)

    active_alerts = CapAlertPage.objects.filter(id__in=active_alert_infos).live()

    geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    for active_alert in active_alerts:
        features = active_alert.get_geojson_features(request)
        if features:
            geojson["features"].extend(features)

    return JsonResponse(geojson)


def get_home_map_alerts(request):
    alerts = CapAlertPage.objects.all().live().filter(status="Actual")
    active_alert_infos = []
    geojson = {"type": "FeatureCollection", "features": []}

    for alert in alerts:
        for info in alert.info:
            if info.value.get('expires') > timezone.localtime():
                start_time = info.value.get("effective") or alert.sent

                if timezone.now() > start_time:
                    status = "Ongoing"
                else:
                    status = "Expected"

                area_desc = [area.get("areaDesc") for area in info.value.area]
                area_desc = ",".join(area_desc)

                alert_info = {
                    "status": status,
                    "url": alert.url,
                    "event": f"{info.value.get('event')} ({area_desc})",
                    "event_icon": info.value.event_icon,
                    "severity": SEVERITY_MAPPING[info.value.get("severity")]
                }

                active_alert_infos.append(alert_info)

                if info.value.features:
                    for feature in info.value.features:
                        geojson["features"].append(feature)
    context = {
        'active_alert_info': active_alert_infos,
        'geojson': json.dumps(geojson)
    }

    return render(request, "home/section/home_map_alerts_include.html", context)


def get_latest_active_alert(request):
    alerts = CapAlertPage.objects.all().live().filter(status="Actual")
    active_alert_infos = []

    context = {}

    for alert in alerts:
        for alert_info in alert.infos:
            info = alert_info.get("info")
            if info.value.get('expires') > timezone.localtime():
                active_alert_infos.append(alert_info)

    if len(active_alert_infos) == 0:
        context.update({
            'latest_active_alert': None
        })
    else:
        context.update({
            'latest_active_alert': active_alert_infos[0]
        })

    return render(request, "cap/active_alert.html", context)
