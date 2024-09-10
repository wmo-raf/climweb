from django.urls import path

from .views import get_playlist_videos_include

urlpatterns = [
    path("api/videos/<int:pk>", get_playlist_videos_include, name="youtube_playlist_items"),
]
