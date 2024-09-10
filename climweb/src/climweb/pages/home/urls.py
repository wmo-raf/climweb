from django.urls import path

from .views import home_map_settings

urlpatterns = [
    path("api/home-map/settings", home_map_settings, name="home-map-settings"),
]
