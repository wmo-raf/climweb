from django.urls import path

from pages.cap.views import (
    AlertListFeed,
    cap_geojson,
    get_home_map_alerts,
    get_latest_active_alert,
    get_cap_xml,
    get_cap_stylesheet
)

urlpatterns = [
    path("home-map-alerts/", get_home_map_alerts, name="home_map_alerts"),
    path("latest-active-alert/", get_latest_active_alert, name="latest_active_alert"),
    path("api/cap/rss.xml", AlertListFeed(), name="cap_alert_feed"),
    path("api/cap/alerts.geojson", cap_geojson, name="cap_alerts_geojson"),
    path("api/cap/<uuid:identifier>.xml", get_cap_xml, name="cap_alert_xml"),
    path("cap-style.xsl", get_cap_stylesheet, name="cap_stylesheet"),
]
