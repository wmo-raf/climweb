"""
URLs for the wagtail admin dashboard.
"""

from django.urls import path
from django.urls import re_path
from forecast_manager.views import upload_forecast, save_data, get_data

urlpatterns = [
    path("upload_forecast/", upload_forecast, name="upload_forecast"),
    path('save-data/', save_data, name='save_data'),
    re_path(r'^get-data/$', get_data, name='get_data'),


]