from django.urls import path
from .views import ZoomEventView

urlpatterns = [
    path('zoom_batch/<pk>', ZoomEventView.as_view(), name="zoom_batch_detail"),
]