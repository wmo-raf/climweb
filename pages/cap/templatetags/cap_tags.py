from datetime import datetime

from django import template
from django.utils import timezone

from pages.cap.models import CapAlertPage

register = template.Library()


@register.inclusion_tag(filename="cap/active_alert.html")
def get_latest_active_cap_alert():
    alerts = CapAlertPage.objects.all().live().order_by('-sent')
    active_alert_infos = []

    for alert in alerts:
        for alert_info in alert.infos:
            info = alert_info.get("info")
            if info.value.get('expires') > timezone.localtime():
                active_alert_infos.append(alert_info)

    if len(active_alert_infos) == 0:
        return {
            'latest_active_alert': None
        }

    return {
        'latest_active_alert': active_alert_infos[0]
    }
