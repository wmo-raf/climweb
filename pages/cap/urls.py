from django.urls import path

from pages.cap.views import AlertDetail, AlertListFeed, cap_geojson

urlpatterns = [
    path("api/cap/rss.xml", AlertListFeed(), name="cap_alert_feed"),
    path("api/cap/alerts.geojson", cap_geojson, name="cap_alerts_geojson"),
    path("api/cap/<uuid:identifier>.xml", AlertDetail.as_view(), name="cap_alert_detail"),
]
