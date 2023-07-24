from django.urls import path

from .views import eumetsat_get_layer_time_values, get_today_layer_animation_images

urlpatterns = [
    path(r'satellite-imagery/time_value', eumetsat_get_layer_time_values, name="sat_get_layer_time"),
    path(r'satellite-imagery/images', get_today_layer_animation_images, name="sat_get_animation_images"),
]
