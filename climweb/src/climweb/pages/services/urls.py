from django.urls import path

from .views import service_map_settings

urlpatterns = [
    path("api/services/<int:page_id>/map-settings", service_map_settings, name="service-map-settings"),
]
