from django.urls import path

from .views import get_audio_playlist_embed

urlpatterns = [
    path("api/audio-playlists/<int:pk>", get_audio_playlist_embed, name="audio_playlist_embed"),
]
