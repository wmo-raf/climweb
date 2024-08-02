from django.urls import path

from pages.aviation.views import get_messages, get_latest_message_datetimes

urlpatterns = [
    path('get_messages/', get_messages, name='get_messages'),
    path('get_latest_message_datetimes/', get_latest_message_datetimes, name='get_latest_message_datetimes'),

]
