from django.urls import path

from pages.aviation.views import get_messages, get_latest_message_datetimes, wind_barb_icons, cloud_cover_icons

urlpatterns = [
    path('get_messages/', get_messages, name='get_messages'),
    path('wind-barb-icons/', wind_barb_icons, name='wind-barb-icons'),
    path('cloud-cover-icons/', cloud_cover_icons, name='cloud-cover-icons'),
    path('get_latest_message_datetimes/', get_latest_message_datetimes, name='get_latest_message_datetimes'),
]
