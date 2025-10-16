from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem

from .models import StationSettings
from .utils import create_stations_geomanager_dataset
from .views import load_stations, preview_stations


@hooks.register('register_admin_urls')
def urlconf_stations():
    return [
        path('load-stations/', load_stations, name='load_stations'),
        path('preview-stations/', preview_stations, name='preview_stations'),
    ]


@hooks.register('construct_settings_menu')
def hide_settings_menu_item(request, menu_items):
    hidden_settings = ["station-settings"]
    menu_items[:] = [item for item in menu_items if item.name not in hidden_settings]


@hooks.register('register_geo_manager_menu_item')
def add_stations_loader_to_geomanager():
    stations_data = MenuItem(label=_("Stations Data"), url=reverse("preview_stations"), icon_name="map")
    return stations_data


@hooks.register('register_geo_manager_menu_item')
def add_stations_settings_to_geomanager():
    settings_url = reverse("wagtailsettings:edit",
                           args=[StationSettings._meta.app_label, StationSettings._meta.model_name, ], )
    station_settings_menu = MenuItem(label=_("Station Settings"), url=settings_url, icon_name="cog")
    return station_settings_menu


@hooks.register('register_geomanager_datasets')
def add_geomanager_datasets(request):
    datasets = []
    station_settings = StationSettings.for_request(request)
    if station_settings.show_on_mapviewer and station_settings.geomanager_subcategory:
        dataset = create_stations_geomanager_dataset(station_settings, request)
        if dataset:
            datasets.append(dataset)

    return datasets
