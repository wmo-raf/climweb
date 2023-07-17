from django.urls import path

from .views import eumetsat_get_layer_time_values

urlpatterns = [
    path(r'eumetview/time-values', eumetsat_get_layer_time_values, name="eumetview_get_layer_time"),
]
