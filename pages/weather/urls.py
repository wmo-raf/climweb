from django.urls import path
from .views import get_home_forecast_widget

urlpatterns = [
    path('home-weather-widget/', get_home_forecast_widget, name="home-weather-widget"),
]
