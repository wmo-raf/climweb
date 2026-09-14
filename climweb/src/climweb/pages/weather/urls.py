from django.urls import path

from .views import get_cities_with_forecast_data, get_home_forecast_widget, get_home_map_forecast

urlpatterns = [
    path('home-weather-widget/', get_home_forecast_widget, name="home-weather-widget"),
    path('home-weather-forecast/', get_home_map_forecast, name="home-weather-forecast"),
    path('cities-with-forecast-data/', get_cities_with_forecast_data, name="cities-with-forecast-data"),
]
