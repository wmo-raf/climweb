from django.urls import path

from .views import get_home_forecast_widget, get_home_map_forecast, get_city_locations

urlpatterns = [
    path('home-weather-widget/', get_home_forecast_widget, name="home-weather-widget"),
    path('home-weather-forecast/', get_home_map_forecast, name="home-weather-forecast"),
    path('weather-city-locations/', get_city_locations, name="weather-city-locations"),

]
