from unittest import mock

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from wagtail.test.utils import WagtailPageTestCase

from climweb.pages.home.tests.factories import get_or_create_homepage
from climweb.pages.mediacenter.tests.factories import MediaIndexPageFactory
from climweb.pages.organisation_pages.organisation.tests.factories import OrganisationIndexPageFactory
from climweb.pages.organisation_pages.projects.tests.factories import ProjectsIndexPageFactory, ProjectPageFactory
from climweb.pages.products.tests.factories import ProductIndexPageFactory, ProductPageFactory
from climweb.pages.services.tests.factories import ServiceIndexPageFactory, ServicePageFactory
from .factories import AudioPlaylistFactory
from ..models import AudioPlaylist, AudioPlatform

LOCMEM_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "audio-playlist-tests",
    }
}

SAMPLE_FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Meteo Togo Podcast</title>
    <link>https://example.org/podcast</link>
    <itunes:author>ANAMET</itunes:author>
    <itunes:image href="https://example.org/artwork.jpg"/>
    <item>
      <title>Episode 2: Rainy season outlook</title>
      <link>https://example.org/podcast/2</link>
      <pubDate>Mon, 06 Oct 2025 08:00:00 +0000</pubDate>
      <description><![CDATA[<p>What to expect <b>this</b> season.</p>]]></description>
      <itunes:duration>12:34</itunes:duration>
      <enclosure url="https://example.org/audio/2.mp3" type="audio/mpeg" length="1234"/>
    </item>
    <item>
      <title>No audio here</title>
      <link>https://example.org/podcast/none</link>
    </item>
    <item>
      <title>Episode 1: Welcome</title>
      <link>https://example.org/podcast/1</link>
      <pubDate>Mon, 29 Sep 2025 08:00:00 +0000</pubDate>
      <enclosure url="https://example.org/audio/1.mp3" type="audio/mpeg" length="1234"/>
    </item>
  </channel>
</rss>
"""

SOUNDCLOUD_OEMBED = {
    "title": "Climate Briefings",
    "author_name": "Meteo Togo",
    "author_url": "https://soundcloud.com/meteo-togo",
    "thumbnail_url": "https://i1.sndcdn.com/artworks-000.jpg",
    "html": '<iframe width="100%" height="450" scrolling="no" frameborder="no" '
            'src="https://w.soundcloud.com/player/?visual=true&url=https%3A%2F%2Fapi.soundcloud.com%2Fplaylists%2F1234567'
            '&show_artwork=true"></iframe>',
}


class FakeResponse:
    def __init__(self, content=b"", json_data=None, status=200):
        self.content = content
        self._json = json_data
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._json


class TestEmbedUrls(TestCase):
    def test_youtube_music_playlist(self):
        playlist = AudioPlaylist(platform=AudioPlatform.YOUTUBE_MUSIC,
                                 playlist_url="https://music.youtube.com/playlist?list=PLabc_123-XYZ&si=foo")
        self.assertEqual(playlist.youtube_playlist_id, "PLabc_123-XYZ")
        self.assertEqual(playlist.get_embed_url(),
                         "https://www.youtube.com/embed/videoseries?list=PLabc_123-XYZ&rel=0&modestbranding=1&playsinline=1")

    def test_youtube_music_requires_list_param(self):
        playlist = AudioPlaylist(platform=AudioPlatform.YOUTUBE_MUSIC,
                                 playlist_url="https://music.youtube.com/watch?v=abc")
        self.assertIsNone(playlist.get_embed_url())

    def test_spotify_show_and_playlist(self):
        show = AudioPlaylist(platform=AudioPlatform.SPOTIFY,
                             playlist_url="https://open.spotify.com/show/4rOoJ6Egrf8K2IrywzwOMk?si=x")
        self.assertEqual(show.get_embed_url(), "https://open.spotify.com/embed/show/4rOoJ6Egrf8K2IrywzwOMk?theme=0")

        playlist = AudioPlaylist(platform=AudioPlatform.SPOTIFY,
                                 playlist_url="https://open.spotify.com/intl-fr/playlist/37i9dQZF1DXcBWIGoYBM5M")
        self.assertEqual(playlist.get_embed_url(),
                         "https://open.spotify.com/embed/playlist/37i9dQZF1DXcBWIGoYBM5M?theme=0")

    def test_apple_podcasts_show_and_episode(self):
        show = AudioPlaylist(platform=AudioPlatform.APPLE_PODCASTS,
                             playlist_url="https://podcasts.apple.com/fr/podcast/meteo-togo/id1234567890")
        self.assertEqual(show.get_embed_url(), "https://embed.podcasts.apple.com/fr/podcast/id1234567890")

        episode = AudioPlaylist(platform=AudioPlatform.APPLE_PODCASTS,
                                playlist_url="https://podcasts.apple.com/fr/podcast/meteo-togo/id1234567890?i=1000")
        self.assertEqual(episode.get_embed_url(), "https://embed.podcasts.apple.com/fr/podcast/id1234567890?i=1000")

    def test_soundcloud_uses_permalink_when_unresolved(self):
        playlist = AudioPlaylist(platform=AudioPlatform.SOUNDCLOUD,
                                 playlist_url="https://soundcloud.com/meteo-togo/sets/briefings")
        url = playlist.get_embed_url()
        self.assertTrue(url.startswith("https://w.soundcloud.com/player/?"))
        self.assertIn("url=https%3A%2F%2Fsoundcloud.com%2Fmeteo-togo%2Fsets%2Fbriefings", url)
        self.assertIn("auto_play=false", url)

    def test_soundcloud_uses_resolved_api_url(self):
        playlist = AudioPlaylist(platform=AudioPlatform.SOUNDCLOUD,
                                 playlist_url="https://soundcloud.com/meteo-togo/sets/briefings")
        url = playlist.get_embed_url(soundcloud_resource_url="https://api.soundcloud.com/playlists/1234567")
        self.assertIn("url=https%3A%2F%2Fapi.soundcloud.com%2Fplaylists%2F1234567", url)


class TestValidation(TestCase):
    def test_platform_url_mismatch(self):
        playlist = AudioPlaylist(title="x", platform=AudioPlatform.SOUNDCLOUD,
                                 playlist_url="https://open.spotify.com/show/4rOoJ6Egrf8K2IrywzwOMk")
        with self.assertRaises(ValidationError) as ctx:
            playlist.full_clean()
        self.assertIn("playlist_url", ctx.exception.message_dict)

    def test_youtube_without_playlist_id(self):
        playlist = AudioPlaylist(title="x", platform=AudioPlatform.YOUTUBE_MUSIC,
                                 playlist_url="https://www.youtube.com/watch?v=abc")
        with self.assertRaises(ValidationError):
            playlist.full_clean()

    def test_apple_bad_path(self):
        playlist = AudioPlaylist(title="x", platform=AudioPlatform.APPLE_PODCASTS,
                                 playlist_url="https://podcasts.apple.com/fr/browse")
        with self.assertRaises(ValidationError):
            playlist.full_clean()

    def test_valid_links_pass(self):
        valid = [
            (AudioPlatform.SOUNDCLOUD, "https://soundcloud.com/meteo-togo/sets/briefings"),
            (AudioPlatform.SOUNDCLOUD, "https://on.soundcloud.com/abc123"),
            (AudioPlatform.YOUTUBE_MUSIC, "https://music.youtube.com/playlist?list=PLabc"),
            (AudioPlatform.YOUTUBE_MUSIC, "https://www.youtube.com/playlist?list=PLabc"),
            (AudioPlatform.SPOTIFY, "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"),
            (AudioPlatform.APPLE_PODCASTS, "https://podcasts.apple.com/us/podcast/id123"),
            (AudioPlatform.RSS, "https://anchor.fm/s/abc/podcast/rss"),
        ]
        for platform, url in valid:
            AudioPlaylist(title="x", platform=platform, playlist_url=url).full_clean()


@override_settings(CACHES=LOCMEM_CACHE)
class TestRemoteDetails(TestCase):
    def setUp(self):
        cache.clear()

    @mock.patch("climweb.pages.audio.models.requests.get")
    def test_rss_feed_parsing(self, mocked_get):
        mocked_get.return_value = FakeResponse(content=SAMPLE_FEED)
        playlist = AudioPlaylistFactory(platform=AudioPlatform.RSS, playlist_url="https://example.org/feed.xml")

        context = playlist.get_embed_context()

        self.assertIsNone(context["embed_url"])
        episodes = context["episodes"]
        self.assertEqual(len(episodes), 2)  # the item without an enclosure is skipped
        self.assertEqual(episodes[0]["title"], "Episode 2: Rainy season outlook")
        self.assertEqual(episodes[0]["audio_url"], "https://example.org/audio/2.mp3")
        self.assertEqual(episodes[0]["audio_type"], "audio/mpeg")
        self.assertEqual(episodes[0]["duration"], "12:34")
        self.assertEqual(episodes[0]["published"].year, 2025)
        self.assertEqual(episodes[0]["summary"], "What to expect this season.")
        self.assertEqual(context["details"]["title"], "Meteo Togo Podcast")
        self.assertEqual(context["details"]["author"], "ANAMET")
        self.assertEqual(context["details"]["thumbnail"], "https://example.org/artwork.jpg")

    @mock.patch("climweb.pages.audio.models.requests.get")
    def test_rss_details_are_cached_until_saved(self, mocked_get):
        mocked_get.return_value = FakeResponse(content=SAMPLE_FEED)
        playlist = AudioPlaylistFactory(platform=AudioPlatform.RSS, playlist_url="https://example.org/feed.xml")

        playlist.get_details()
        playlist.get_details()
        self.assertEqual(mocked_get.call_count, 1)

        # saving the snippet forces a refresh
        playlist.save()
        playlist.get_details()
        self.assertEqual(mocked_get.call_count, 2)

    @mock.patch("climweb.pages.audio.models.requests.get")
    def test_rss_failure_is_not_cached(self, mocked_get):
        mocked_get.side_effect = RuntimeError("boom")
        playlist = AudioPlaylistFactory(platform=AudioPlatform.RSS, playlist_url="https://example.org/feed.xml")

        self.assertIsNone(playlist.get_embed_context())
        self.assertIsNone(playlist.get_embed_context())
        self.assertEqual(mocked_get.call_count, 2)

    @mock.patch("climweb.pages.audio.models.requests.get")
    def test_soundcloud_oembed_resolution(self, mocked_get):
        mocked_get.return_value = FakeResponse(json_data=SOUNDCLOUD_OEMBED)
        playlist = AudioPlaylistFactory(platform=AudioPlatform.SOUNDCLOUD,
                                        playlist_url="https://soundcloud.com/meteo-togo/sets/briefings")

        context = playlist.get_embed_context()

        self.assertEqual(context["details"]["resource_url"], "https://api.soundcloud.com/playlists/1234567")
        self.assertEqual(context["details"]["author"], "Meteo Togo")
        self.assertIn("url=https%3A%2F%2Fapi.soundcloud.com%2Fplaylists%2F1234567", context["embed_url"])
        self.assertEqual(context["embed_height"], 450)

        kwargs = mocked_get.call_args.kwargs
        self.assertEqual(kwargs["params"]["url"], "https://soundcloud.com/meteo-togo/sets/briefings")

    @mock.patch("climweb.pages.audio.models.requests.get")
    def test_soundcloud_falls_back_to_permalink_when_oembed_fails(self, mocked_get):
        mocked_get.side_effect = RuntimeError("boom")
        playlist = AudioPlaylistFactory(platform=AudioPlatform.SOUNDCLOUD,
                                        playlist_url="https://soundcloud.com/meteo-togo/sets/briefings")

        context = playlist.get_embed_context()
        self.assertIn("url=https%3A%2F%2Fsoundcloud.com%2Fmeteo-togo%2Fsets%2Fbriefings", context["embed_url"])

    def test_iframe_platforms_need_no_network(self):
        with mock.patch("climweb.pages.audio.models.requests.get") as mocked_get:
            playlist = AudioPlaylistFactory()  # spotify
            context = playlist.get_embed_context()
        mocked_get.assert_not_called()
        self.assertEqual(context["embed_url"], "https://open.spotify.com/embed/show/4rOoJ6Egrf8K2IrywzwOMk?theme=0")


@override_settings(CACHES=LOCMEM_CACHE)
class TestEmbedView(TestCase):
    def setUp(self):
        cache.clear()

    def test_renders_iframe_player(self):
        playlist = AudioPlaylistFactory(title="Weekly briefing", description="Our weekly show")
        resp = self.client.get(reverse("audio_playlist_embed", args=[playlist.pk]))

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'src="https://open.spotify.com/embed/show/4rOoJ6Egrf8K2IrywzwOMk?theme=0"')
        self.assertContains(resp, 'title="Weekly briefing (Spotify)"')
        self.assertContains(resp, "Open on Spotify")
        self.assertContains(resp, "Our weekly show")
        self.assertIn("no-store", resp["Cache-Control"])

    @mock.patch("climweb.pages.audio.models.requests.get")
    def test_renders_native_podcast_player(self, mocked_get):
        mocked_get.return_value = FakeResponse(content=SAMPLE_FEED)
        playlist = AudioPlaylistFactory(platform=AudioPlatform.RSS, playlist_url="https://example.org/feed.xml")

        resp = self.client.get(reverse("audio_playlist_embed", args=[playlist.pk]))

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "<audio controls", count=2)
        self.assertContains(resp, 'src="https://example.org/audio/2.mp3"')
        self.assertContains(resp, "Episode 2: Rainy season outlook")

    @mock.patch("climweb.pages.audio.models.requests.get")
    def test_empty_response_when_unavailable(self, mocked_get):
        mocked_get.side_effect = RuntimeError("boom")
        playlist = AudioPlaylistFactory(platform=AudioPlatform.RSS, playlist_url="https://example.org/feed.xml")

        resp = self.client.get(reverse("audio_playlist_embed", args=[playlist.pk]))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"")

    def test_unknown_playlist(self):
        resp = self.client.get(reverse("audio_playlist_embed", args=[999999]))
        self.assertEqual(resp.status_code, 404)


class TestPagesWithAudioPlaylists(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        home_page = get_or_create_homepage()
        cls.playlist = AudioPlaylistFactory(title="Seasonal outlook show")
        playlists = [("playlist", cls.playlist)]

        cls.media_page = MediaIndexPageFactory(parent=home_page, audio_playlists=playlists)

        services_index = ServiceIndexPageFactory(parent=home_page)
        cls.service_page = ServicePageFactory(parent=services_index, audio_playlists=playlists)

        products_index = ProductIndexPageFactory(parent=home_page)
        cls.product_page = ProductPageFactory(parent=products_index, audio_playlists=playlists)

        organisation_page = OrganisationIndexPageFactory(parent=home_page)
        projects_index = ProjectsIndexPageFactory(parent=organisation_page)
        cls.project_page = ProjectPageFactory(parent=projects_index, audio_playlists=playlists)

        cls.plain_service_page = ServicePageFactory(parent=services_index)

    def assertHasAudioSection(self, page):
        self.assertPageIsRenderable(page)
        resp = self.client.get(page.get_url())
        self.assertContains(resp, 'id="audioSection"')
        self.assertContains(resp, 'data-audio-playlist')
        self.assertContains(resp, reverse("audio_playlist_embed", args=[self.playlist.pk]))
        self.assertContains(resp, "audio_playlist.css")

    def test_media_page(self):
        self.assertHasAudioSection(self.media_page)

    def test_service_page(self):
        self.assertHasAudioSection(self.service_page)

    def test_product_page(self):
        self.assertHasAudioSection(self.product_page)

    def test_project_page(self):
        self.assertHasAudioSection(self.project_page)

    def test_page_without_playlists_has_no_section(self):
        resp = self.client.get(self.plain_service_page.get_url())
        self.assertNotContains(resp, 'id="audioSection"')
