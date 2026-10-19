import factory

from ..models import AudioPlaylist, AudioPlatform


class AudioPlaylistFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AudioPlaylist

    title = factory.Sequence(lambda n: f"Playlist {n}")
    platform = AudioPlatform.SPOTIFY
    playlist_url = "https://open.spotify.com/show/4rOoJ6Egrf8K2IrywzwOMk"
