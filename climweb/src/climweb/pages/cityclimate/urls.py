from django.urls import path

from .views import climate_data, city_climate_chart_thumbnail

urlpatterns = [
    path("data/<int:page_id>/", climate_data, name="climate_data"),
    path("thumbnail/<int:page_id>/", city_climate_chart_thumbnail, name="city_climate_chart_thumbnail"),
]
