"""
URLs for the wagtail admin dashboard.
"""

from django.urls import path
from forecast_manager.views import upload_forecast

urlpatterns = [
    path("upload_forecast/", upload_forecast, name="upload_forecast"),
]