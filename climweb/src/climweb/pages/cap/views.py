import json
from typing import List

from capeditor.constants import SEVERITY_MAPPING
from capeditor.models import CapSetting
from django.contrib.syndication.views import Feed
from django.core.validators import validate_email
from django.db.models.base import Model
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.feedgenerator import Enclosure, rfc2822_date
from django.utils.feedgenerator import Rss201rev2Feed
from django.utils.translation import gettext as _
from django.utils.xmlutils import SimplerXMLGenerator
from wagtail.models import Site

from climweb.base.cache import wagcache
from .models import (
    CapAlertPage,
    OtherCAPSettings,
)
from .utils import (
    serialize_and_sign_cap_alert,
    get_currently_active_alerts,
    get_all_published_alerts
)


class CustomCAPFeed(Rss201rev2Feed):
    content_type = 'application/xml'

    def write(self, outfile, encoding):
        handler = SimplerXMLGenerator(outfile, encoding, short_empty_elements=True)
        handler.startDocument()

        # add stylesheet
        handler.processingInstruction('xml-stylesheet', f'type="text/xsl" href="{reverse("cap_feed_stylesheet")}"')

        handler.startElement("rss", self.rss_attributes())
        handler.startElement("channel", self.root_attributes())
        self.add_root_elements(handler)
        self.write_items(handler)
        self.endChannelElement(handler)
        handler.endElement("rss")

    def add_root_elements(self, handler):
        super().add_root_elements(handler)
        pubDate = rfc2822_date(self.latest_post_date())
        handler.addQuickElement('pubDate', pubDate)

        try:
            site = Site.objects.get(is_default_site=True)
            if site:
                cap_setting = CapSetting.for_site(site)
                logo = cap_setting.logo
                sender_name = cap_setting.sender_name

                if logo:
                    url = logo.get_rendition('original').url
                    url = site.root_url + url

                    if url:
                        # add logo image
                        handler.startElement('image', {})
                        handler.addQuickElement('url', url)

                        if sender_name:
                            handler.addQuickElement('title', sender_name)

                        if self.feed.get('link'):
                            handler.addQuickElement('link', site.root_url)

                        handler.endElement('image')

        except Exception as e:
            pass

    def add_item_elements(self, handler, item):
        handler.addQuickElement("title", item["title"])
        handler.addQuickElement("link", item["link"])
        if item["description"] is not None:
            handler.addQuickElement("description", item["description"])

        # Author information.
        if item["author_name"] and item["author_email"]:
            handler.addQuickElement(
                "author", "%s (%s)" % (item["author_email"], item["author_name"])
            )
        elif item["author_email"]:
            handler.addQuickElement("author", item["author_email"])
        elif item["author_name"]:
            handler.addQuickElement(
                "dc:creator",
                item["author_name"],
                {"xmlns:dc": "http://purl.org/dc/elements/1.1/"},
            )

        if item["pubdate"] is not None:
            handler.addQuickElement("pubDate", rfc2822_date(item["pubdate"]))
        if item["comments"] is not None:
            handler.addQuickElement("comments", item["comments"])
        if item["unique_id"] is not None:
            guid_attrs = {}
            if isinstance(item.get("unique_id_is_permalink"), bool):
                guid_attrs["isPermaLink"] = str(item["unique_id_is_permalink"]).lower()
            handler.addQuickElement("guid", item["unique_id"], guid_attrs)
        if item["ttl"] is not None:
            handler.addQuickElement("ttl", item["ttl"])

        # Categories.
        for cat in item["categories"]:
            handler.addQuickElement("category", cat)


class AlertListFeed(Feed):
    feed_copyright = "public domain"
    language = "en"

    feed_type = CustomCAPFeed

    @staticmethod
    def link():
        return reverse("cap_alert_feed")

    def title(self):
        title = _("Latest alerts")

        try:
            site = Site.objects.get(is_default_site=True)
            if site:
                cap_setting = CapSetting.for_site(site)
                if cap_setting.sender_name:
                    title = _("Latest alerts from %(sender_name)s") % {"sender_name": cap_setting.sender_name}
        except Exception:
            pass

        return title

    def description(self):
        description = _("Latest alerts")

        try:
            site = Site.objects.get(is_default_site=True)
            if site:
                cap_setting = CapSetting.for_site(site)
                if cap_setting.sender_name:
                    description = _("Latest alerts from %(sender_name)s") % {"sender_name": cap_setting.sender_name}
        except Exception:
            pass

        return description

    def items(self):
        alerts = get_all_published_alerts()
        return alerts

    def item_title(self, item):
        return item.title

    def item_link(self, item):
        return reverse("cap_alert_xml", args=[item.guid])

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
        categories = item.info[0].value.get('category')

        if isinstance(categories, str):
            categories = [categories]

        return categories


def get_cap_xml(request, guid):
    alert = get_object_or_404(CapAlertPage, guid=guid)
    xml = wagcache.get(f"cap_alert_xml_{guid}")

    if not xml:
        xml, signed = serialize_and_sign_cap_alert(alert, request)
        xml = xml.decode("utf-8")

        if signed:
            # cache signed alerts for 5 days
            wagcache.set(f"cap_alert_xml_{guid}", xml, 60 * 60 * 24 * 5)

    return HttpResponse(xml, content_type="application/xml")


def get_cap_feed_stylesheet(request):
    stylesheet = wagcache.get("cap_feed_stylesheet")

    if not stylesheet:
        stylesheet = render_to_string("cap/cap-feed-stylesheet.html").strip()
        # cache for 5 days
        wagcache.set("cap_feed_stylesheet", stylesheet, 60 * 60 * 24 * 5)

    return HttpResponse(stylesheet, content_type="application/xml")


def get_cap_alert_stylesheet(request):
    stylesheet = wagcache.get("cap_alert_stylesheet")

    if not stylesheet:
        stylesheet = render_to_string("cap/cap-alert-stylesheet.html").strip()
        # cache for 5 days
        wagcache.set("cap_alert_stylesheet", stylesheet, 60 * 60 * 24 * 5)

    return HttpResponse(stylesheet, content_type="application/xml")


def cap_geojson(request):
    active_alerts = get_currently_active_alerts()

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
    alerts = get_currently_active_alerts()
    active_alert_infos = []
    geojson = {"type": "FeatureCollection", "features": []}

    cap_settings = OtherCAPSettings.for_request(request)
    default_alert_display_language = cap_settings.default_alert_display_language

    for alert in alerts:
        # take the first info
        info = alert.info[0]

        if default_alert_display_language and len(alert.info) > 1:
            for info_item in alert.info:
                info_lang = info_item.value.get("language")
                if info_lang == default_alert_display_language.code or info_lang.startswith(
                        default_alert_display_language.code):
                    info = info_item
                    break

        start_time = info.value.get("effective") or alert.sent

        if timezone.localtime() > start_time:
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
        'has_alerts': len(active_alert_infos) > 0,
        'active_alert_info': active_alert_infos,
        'geojson': json.dumps(geojson)
    }

    return render(request, "home/section/home_map_alerts_include.html", context)


def get_latest_active_alert(request):
    other_cap_settings = OtherCAPSettings.for_request(request)
    active_alert_style = other_cap_settings.active_alert_style or "nav_left"
    default_alert_display_language = other_cap_settings.default_alert_display_language

    alerts = get_currently_active_alerts()
    active_alert_infos = []

    context = {}

    for alert in alerts:
        alert_info = alert.infos[0]
        for alert_info in alert.infos:
            if default_alert_display_language and len(alert.info) > 1:
                for info_item in alert.infos:
                    info_lang = info_item.get("info").value.get("language")
                    if info_lang == default_alert_display_language.code or info_lang.startswith(
                            default_alert_display_language.code):
                        alert_info = info_item
                        break

        alert_info.update({"title": alert.title, })
        active_alert_infos.append(alert_info)

    if len(active_alert_infos) == 0:
        context.update({
            'latest_active_alert': None
        })
    else:
        context.update({
            'latest_active_alert': active_alert_infos[0],
            'alert_style': active_alert_style
        })

    if active_alert_style == "nav_left":
        return render(request, "cap/widgets/nav_left_alert.html", context)

    if active_alert_style == "nav_top":
        return render(request, "cap/widgets/nav_top_alert.html", context)

    return render(request, "cap/widgets/nav_left_alert.html", context)
