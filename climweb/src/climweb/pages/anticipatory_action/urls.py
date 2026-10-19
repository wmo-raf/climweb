from django.urls import path

from .views import anticipatory_action_map_settings, anticipatory_action_cap_geojson

urlpatterns = [
    path("api/anticipatory-action/<int:page_id>/map-settings", anticipatory_action_map_settings,
         name="anticipatory-action-map-settings"),
    path("api/anticipatory-action/<int:page_id>/cap-alerts.geojson", anticipatory_action_cap_geojson,
         name="anticipatory-action-cap-geojson"),
]
