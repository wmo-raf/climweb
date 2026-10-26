"""
Selection of the CAP alerts relevant to an Anticipatory Action page.

capcomposer is optional, so everything here returns empty results when it is not installed.
"""
from django.conf import settings
from loguru import logger
from shapely.geometry import shape


def is_cap_installed():
    return "capcomposer.cap" in settings.INSTALLED_APPS


def get_hazard_event_type_choices(site):
    if not site or not is_cap_installed():
        return []

    from capcomposer.capeditor.blocks import get_hazard_types
    return get_hazard_types(site)


def info_matches(info_value, event_types, area_geometries):
    """
    Check if a single CAP alert info block matches the page filters.
    Empty filters match everything.
    """
    if event_types and info_value.get("event") not in event_types:
        return False

    if not area_geometries:
        return True

    for feature in info_value.features or []:
        geometry = feature.get("geometry")
        if not geometry:
            continue
        try:
            info_geometry = shape(geometry)
        except Exception as e:
            logger.warning(f"[ANTICIPATORY_ACTION]: Invalid CAP area geometry: {e}")
            continue

        if any(info_geometry.intersects(area) for area in area_geometries):
            return True

    return False


def alert_matches(alert, event_types, area_geometries):
    return any(info_matches(info.value, event_types, area_geometries) for info in alert.info)


def get_matching_active_alerts(page):
    """
    Currently active CAP alerts matching the page's event types and areas,
    with the page's featured alert first if it is still active
    """
    if not is_cap_installed():
        return []

    from capcomposer.cap.utils import get_currently_active_alerts

    event_types = set(page.cap_event_types or [])
    area_geometries = page.cap_area_geometries

    alerts = [alert for alert in get_currently_active_alerts()
              if alert_matches(alert, event_types, area_geometries)]

    featured = page.active_featured_cap_alert
    if featured:
        alerts = [featured] + [alert for alert in alerts if alert.pk != featured.pk]

    return alerts


def get_default_language_info(alert, request=None):
    """
    The alert info in the site's default CAP display language, or the first one
    """
    from capcomposer.cap.models import OtherCAPSettings

    infos = alert.infos
    default_info = infos[0]

    if len(infos) > 1:
        if request:
            cap_settings = OtherCAPSettings.for_request(request)
        else:
            cap_settings = OtherCAPSettings.for_site(alert.get_site())

        default_language = cap_settings.default_alert_display_language
        if default_language:
            for info_item in infos:
                info_lang = info_item.get("info").value.get("language") or ""
                if info_lang == default_language.code or info_lang.startswith(default_language.code):
                    return info_item

    return default_info


def get_alert_display_infos(alerts, request=None):
    """
    Data for rendering the alerts on the page, including the instructions to the population
    """
    display_infos = []

    for alert in alerts:
        info_item = get_default_language_info(alert, request)
        info_value = info_item.get("info").value

        area_desc = ", ".join([area.get("areaDesc") for area in info_value.area])

        display_infos.append({
            "url": alert.url,
            "event": info_item.get("event"),
            "event_icon": info_item.get("event_icon"),
            "area_desc": area_desc,
            "status": info_item.get("status"),
            "severity": info_item.get("severity"),
            "urgency": info_item.get("urgency"),
            "certainty": info_item.get("certainty"),
            "sent": alert.sent,
            "effective": info_item.get("effective"),
            "expires": info_item.get("expires"),
            "headline": info_value.get("headline"),
            "description": info_value.get("description"),
            "instruction": info_value.get("instruction"),
            # same shape as capcomposer's home map alerts, to reuse its template
            "properties": {
                "headline": info_value.get("headline"),
                "sent": alert.sent,
            },
        })

    return display_infos


def get_alerts_geojson(alerts, request=None):
    geojson = {"type": "FeatureCollection", "features": []}

    for alert in alerts:
        features = alert.get_geojson_features(request)
        if features:
            geojson["features"].extend(features)

    return geojson



def get_active_alert(alert_page_id):
    """
    The alert with the given page id, if it is still active (live, not expired and not cancelled)
    """
    if not alert_page_id or not is_cap_installed():
        return None
    
    from capcomposer.cap.utils import get_currently_active_alerts
    return get_currently_active_alerts().filter(pk=alert_page_id).first()
