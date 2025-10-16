from django.urls import path

from .views import climate_data

urlpatterns = [
    path("data/<int:page_id>/", climate_data, name="climate_data"),
]
