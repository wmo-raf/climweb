from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem

from .views import load_stations, preview_stations


@hooks.register('register_admin_urls')
def urlconf_stations():
    return [
        path('load-stations/', load_stations, name='load_stations'),
        path('preview-stations/', preview_stations, name='preview_stations'),
    ]


@hooks.register('register_geo_manager_menu_item')
def add_stations_to_geomanager():
    stations_data = MenuItem(label=_("Stations Data"), url=reverse("preview_stations"), icon_name="map")
    return stations_data
