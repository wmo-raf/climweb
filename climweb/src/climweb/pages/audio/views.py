import logging

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache

from .models import AudioPlaylist

logger = logging.getLogger(__name__)


@never_cache
def get_audio_playlist_embed(request, pk):
    """
    Returns the rendered player for a playlist. Loaded asynchronously by pages so that
    slow or unavailable platforms never block page rendering. An empty response tells
    the page to hide the player.
    """
    playlist = get_object_or_404(AudioPlaylist, pk=pk)
    try:
        context = playlist.get_embed_context()
    except Exception as e:
        logger.warning("Audio playlist %s could not be rendered: %s", pk, e)
        context = None

    if not context:
        return HttpResponse("")

    return render(request, "audio/playlist_embed_include.html", context)
