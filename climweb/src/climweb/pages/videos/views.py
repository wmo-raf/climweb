from django.shortcuts import render, get_object_or_404

from .models import YoutubePlaylist


def get_playlist_videos_include(request, pk):
    playlist = get_object_or_404(YoutubePlaylist, pk=pk)
    videos = playlist.playlist_items()
    if videos:
        videos = videos[:3]

    return render(request, context={'videos': videos, "playlist": playlist}, template_name='videos_include.html')
