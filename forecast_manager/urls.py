"""
URLs for the wagtail admin dashboard.
"""

from django.urls import path
from django.urls import re_path
from forecast_manager.views import add_forecast, save_data, get_data

urlpatterns = [
    # path("list_forecast/", list_forecasts, name="list_forecasts"),
    path("add_forecast/", add_forecast, name="add_forecast"),
    path('save-data/', save_data, name='save_data'),
    re_path(r'^get-data/$', get_data, name='get_data'),


]