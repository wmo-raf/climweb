from django.urls import path

from pages.cap.views import AlertDetail, AlertListFeed

urlpatterns = [
    path("api/cap/rss.xml", AlertListFeed(), name="cap_alert_feed"),
    path("api/cap/<uuid:identifier>.xml", AlertDetail.as_view(), name="cap_alert_detail"),
]
