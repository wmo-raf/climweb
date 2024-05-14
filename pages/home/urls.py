from django.urls import path

from .views import home_map_settings, wdqms_reports

urlpatterns = [
    path("api/home-map/settings", home_map_settings, name="home-map-settings"),
    path("wdqms-reports/", wdqms_reports, name="wdqms-reports"),
]
