from django.urls import path

from pages.aviation.views import aviation, station_data_geojson, get_messages, get_latest_message_datetimes

urlpatterns = [
    path("aviation/", aviation, name="aviation"),
    path('stations/', station_data_geojson, name='station_data'),
    path('get_messages/', get_messages, name='get_messages'),
    path('get_latest_message_datetimes/', get_latest_message_datetimes, name='get_latest_message_datetimes'),

]
