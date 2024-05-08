from django.urls import path

from pages.cap.views import AlertDetail, AlertListFeed, cap_geojson, get_home_map_alerts, get_latest_active_alert

urlpatterns = [
    path("home-map-alerts/", get_home_map_alerts, name="home_map_alerts"),
    path("latest-active-alert/", get_latest_active_alert, name="latest_active_alert"),
    path("api/cap/rss.xml", AlertListFeed(), name="cap_alert_feed"),
    path("api/cap/alerts.geojson", cap_geojson, name="cap_alerts_geojson"),
    path("api/cap/<uuid:identifier>.xml", AlertDetail.as_view(), name="cap_alert_xml"),
]
