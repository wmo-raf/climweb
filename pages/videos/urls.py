from django.urls import path
from .views import YoutubePlaylistView, YoutubePlaylistItemsView, VideoView

urlpatterns = [
    path('playlists/', YoutubePlaylistView.as_view(), name="playlist_view"),
    path('playlists/<pk>', YoutubePlaylistItemsView.as_view(), name="playlist_items"),
]
