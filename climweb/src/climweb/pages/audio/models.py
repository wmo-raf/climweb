import hashlib
import logging
import re
from html import unescape
from urllib.parse import parse_qs, quote, urlencode, urlparse

import feedparser
import requests
from dateutil.parser import parse as parse_date
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.text import Truncator
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.api.v2.utils import get_full_url
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import EditView, SnippetViewSet

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 10
MAX_RSS_EPISODES = 10
USER_AGENT = "ClimWeb (+https://github.com/wmo-raf/climweb)"


class AudioPlatform(models.TextChoices):
    SOUNDCLOUD = "soundcloud", _("SoundCloud")
    YOUTUBE_MUSIC = "youtube_music", _("YouTube Music / YouTube Podcasts (replaces Google Podcasts)")
    SPOTIFY = "spotify", _("Spotify")
    APPLE_PODCASTS = "apple_podcasts", _("Apple Podcasts")
    RSS = "rss", _("Podcast RSS feed (any host)")


PLATFORM_LABELS = {
    AudioPlatform.SOUNDCLOUD: "SoundCloud",
    AudioPlatform.YOUTUBE_MUSIC: "YouTube Music",
    AudioPlatform.SPOTIFY: "Spotify",
    AudioPlatform.APPLE_PODCASTS: "Apple Podcasts",
    AudioPlatform.RSS: _("Podcast"),
}

# Default iframe heights (px) that fit a full playlist player per platform.
PLATFORM_EMBED_HEIGHTS = {
    AudioPlatform.SOUNDCLOUD: 450,
    AudioPlatform.SPOTIFY: 452,
    AudioPlatform.APPLE_PODCASTS: 450,
}

PLATFORM_HOSTS = {
    AudioPlatform.SOUNDCLOUD: ("soundcloud.com", "on.soundcloud.com", "m.soundcloud.com"),
    AudioPlatform.YOUTUBE_MUSIC: ("youtube.com", "music.youtube.com", "youtu.be"),
    AudioPlatform.SPOTIFY: ("open.spotify.com", "spotify.com"),
    AudioPlatform.APPLE_PODCASTS: ("podcasts.apple.com",),
}

SPOTIFY_PATH_RE = re.compile(r"^/(?:intl-[a-z]{2}(?:-[a-z]{2})?/)?(?:embed/)?(playlist|show|album|episode|track)/([A-Za-z0-9]+)")
APPLE_PATH_RE = re.compile(r"^/([a-z]{2})/podcast/(?:[^/]+/)?id(\d+)")
SOUNDCLOUD_WIDGET_URL_RE = re.compile(r"[?&]url=([^&\"']+)")


def _host_matches(host, allowed_hosts):
    host = (host or "").lower()
    return any(host == h or host.endswith("." + h) for h in allowed_hosts)


def _cache_timeout():
    return getattr(settings, "AUDIO_PLAYLIST_CACHE_TIMEOUT", 60 * 60)


class AudioPlaylist(models.Model):
    """
    An audio playlist, podcast show or set hosted on an external platform, embeddable on pages.

    Google Podcasts was shut down by Google in 2024; its catalogue moved to YouTube Music.
    Playlists that lived on Google Podcasts can be embedded via the YouTube Music option
    (podcasts on YouTube are ordinary playlists) or via the show's RSS feed.
    """
    title = models.CharField(max_length=200, verbose_name=_("Title"))
    platform = models.CharField(
        max_length=30,
        choices=AudioPlatform.choices,
        default=AudioPlatform.SOUNDCLOUD,
        verbose_name=_("Platform"),
        help_text=_("Google Podcasts was discontinued in 2024 and its content moved to YouTube Music. "
                    "Use 'YouTube Music' for playlists that were on Google Podcasts, "
                    "or 'Podcast RSS feed' for a show hosted anywhere."),
    )
    playlist_url = models.URLField(
        max_length=500,
        verbose_name=_("Playlist URL"),
        help_text=_("Public link to the playlist, set, show or feed. Examples: "
                    "https://soundcloud.com/<user>/sets/<playlist>, "
                    "https://music.youtube.com/playlist?list=<id>, "
                    "https://open.spotify.com/show/<id>, "
                    "https://podcasts.apple.com/<country>/podcast/<name>/id<id>, "
                    "or a podcast RSS feed URL."),
    )
    description = models.TextField(blank=True, verbose_name=_("Description"),
                                   help_text=_("Optional short text shown next to the player"))
    refresh_interval_minutes = models.PositiveIntegerField(
        default=60,
        verbose_name=_("Refresh interval (minutes)"),
        help_text=_("How often playlist details are re-fetched from the platform. Embedded players "
                    "always stream the live playlist; this only affects titles, artwork and episode "
                    "lists fetched by the website. Saving this playlist forces an immediate refresh."),
    )

    panels = [
        FieldPanel("title"),
        FieldPanel("platform"),
        FieldPanel("playlist_url"),
        FieldPanel("description"),
        MultiFieldPanel([
            FieldPanel("refresh_interval_minutes"),
        ], heading=_("Auto refresh")),
    ]

    class Meta:
        verbose_name = _("Audio Playlist")
        verbose_name_plural = _("Audio Playlists")

    def __str__(self):
        return self.title

    # ------------------------------------------------------------------ validation
    def clean(self):
        super().clean()
        if not self.playlist_url or not self.platform:
            return
        parsed = urlparse(self.playlist_url)
        if parsed.scheme not in ("http", "https"):
            raise ValidationError({"playlist_url": _("The playlist URL must start with http:// or https://")})

        if self.platform == AudioPlatform.RSS:
            return

        allowed_hosts = PLATFORM_HOSTS.get(self.platform, ())
        if not _host_matches(parsed.netloc, allowed_hosts):
            raise ValidationError({
                "playlist_url": _("This does not look like a %(platform)s link. Expected a link on %(hosts)s") % {
                    "platform": self.get_platform_display(),
                    "hosts": ", ".join(allowed_hosts),
                }
            })

        if self.platform == AudioPlatform.YOUTUBE_MUSIC and not self.youtube_playlist_id:
            raise ValidationError({
                "playlist_url": _("The YouTube Music link must be a playlist link containing 'list=<playlist id>'")})
        if self.platform == AudioPlatform.SPOTIFY and not self.spotify_resource:
            raise ValidationError({
                "playlist_url": _("The Spotify link must point to a playlist, show, album or episode")})
        if self.platform == AudioPlatform.APPLE_PODCASTS and not self.apple_podcast_resource:
            raise ValidationError({
                "playlist_url": _("The Apple Podcasts link must look like "
                                  "https://podcasts.apple.com/<country>/podcast/<name>/id<number>")})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Force an immediate refresh of fetched details next time the playlist is rendered
        self.clear_cache()

    # ------------------------------------------------------------------ helpers
    @property
    def platform_label(self):
        return PLATFORM_LABELS.get(self.platform, self.get_platform_display())

    @property
    def is_rss(self):
        return self.platform == AudioPlatform.RSS

    @property
    def youtube_playlist_id(self):
        parsed = urlparse(self.playlist_url)
        list_id = parse_qs(parsed.query).get("list", [None])[0]
        if list_id and re.fullmatch(r"[A-Za-z0-9_-]+", list_id):
            return list_id
        return None

    @property
    def spotify_resource(self):
        match = SPOTIFY_PATH_RE.match(urlparse(self.playlist_url).path)
        if match:
            return match.group(1), match.group(2)
        return None

    @property
    def apple_podcast_resource(self):
        parsed = urlparse(self.playlist_url)
        match = APPLE_PATH_RE.match(parsed.path)
        if not match:
            return None
        episode_id = parse_qs(parsed.query).get("i", [None])[0]
        if episode_id and not episode_id.isdigit():
            episode_id = None
        return match.group(1), match.group(2), episode_id

    @property
    def embed_height(self):
        return PLATFORM_EMBED_HEIGHTS.get(self.platform)

    def get_embed_api_url(self, request=None):
        api_url = reverse("audio_playlist_embed", args=[self.pk])
        return get_full_url(request, api_url)

    def get_cache_key(self):
        digest = hashlib.md5(f"{self.platform}:{self.playlist_url}".encode("utf-8")).hexdigest()
        return f"audio_playlist:{self.pk}:{digest}"

    def get_cache_timeout(self):
        if self.refresh_interval_minutes:
            return self.refresh_interval_minutes * 60
        return _cache_timeout()

    def clear_cache(self):
        if self.pk:
            cache.delete(self.get_cache_key())

    # ------------------------------------------------------------------ embed urls
    def get_embed_url(self, soundcloud_resource_url=None):
        """
        Return the iframe src for platforms that offer an embeddable player.
        For SoundCloud, pass the resolved api resource url (from oEmbed) when available,
        otherwise the public permalink is used, which the SoundCloud widget also resolves.
        """
        if self.platform == AudioPlatform.SOUNDCLOUD:
            params = {
                "url": soundcloud_resource_url or self.playlist_url,
                "auto_play": "false",
                "hide_related": "true",
                "show_comments": "false",
                "show_user": "true",
                "show_reposts": "false",
                "show_teaser": "false",
                "visual": "false",
            }
            return "https://w.soundcloud.com/player/?" + urlencode(params, quote_via=quote)

        if self.platform == AudioPlatform.YOUTUBE_MUSIC:
            list_id = self.youtube_playlist_id
            if not list_id:
                return None
            return f"https://www.youtube.com/embed/videoseries?list={list_id}&rel=0&modestbranding=1&playsinline=1"

        if self.platform == AudioPlatform.SPOTIFY:
            resource = self.spotify_resource
            if not resource:
                return None
            resource_type, resource_id = resource
            return f"https://open.spotify.com/embed/{resource_type}/{resource_id}?theme=0"

        if self.platform == AudioPlatform.APPLE_PODCASTS:
            resource = self.apple_podcast_resource
            if not resource:
                return None
            country, show_id, episode_id = resource
            url = f"https://embed.podcasts.apple.com/{country}/podcast/id{show_id}"
            if episode_id:
                url += f"?i={episode_id}"
            return url

        return None

    # ------------------------------------------------------------------ remote fetching
    def _get(self, url, **kwargs):
        headers = {"User-Agent": USER_AGENT}
        headers.update(kwargs.pop("headers", {}))
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS, headers=headers, **kwargs)
        response.raise_for_status()
        return response

    def fetch_soundcloud_details(self):
        """
        Resolve the public SoundCloud link through the (key-less) oEmbed endpoint to obtain
        the api resource url used by the widget plus title/author/artwork.
        """
        try:
            response = self._get("https://soundcloud.com/oembed",
                                 params={"format": "json", "url": self.playlist_url})
            data = response.json()
        except Exception as e:
            logger.warning("SoundCloud oEmbed lookup failed for %s: %s", self.playlist_url, e)
            return {}

        resource_url = None
        html = data.get("html") or ""
        match = SOUNDCLOUD_WIDGET_URL_RE.search(html)
        if match:
            resource_url = unescape(match.group(1))
            resource_url = requests.utils.unquote(resource_url)

        return {
            "resource_url": resource_url,
            "title": data.get("title"),
            "author": data.get("author_name"),
            "author_url": data.get("author_url"),
            "thumbnail": data.get("thumbnail_url"),
        }

    def fetch_rss_details(self):
        try:
            response = self._get(self.playlist_url, headers={"Accept": "application/rss+xml, application/xml, text/xml, */*"})
            feed = feedparser.parse(response.content)
        except Exception as e:
            logger.warning("Podcast feed fetch failed for %s: %s", self.playlist_url, e)
            return {}

        episodes = []
        for entry in feed.entries:
            audio_url, audio_type = None, None
            for link in entry.get("enclosures", []) or entry.get("links", []):
                link_type = (link.get("type") or "")
                if link_type.startswith("audio/") or link.get("rel") == "enclosure":
                    audio_url, audio_type = link.get("href"), link_type
                    break
            if not audio_url:
                continue

            published = None
            raw_date = entry.get("published") or entry.get("updated")
            if raw_date:
                try:
                    published = parse_date(raw_date)
                except (ValueError, OverflowError):
                    published = None

            summary = strip_tags(entry.get("summary") or entry.get("subtitle") or "")
            image = None
            if entry.get("image") and entry["image"].get("href"):
                image = entry["image"]["href"]

            episodes.append({
                "title": entry.get("title") or "",
                "link": entry.get("link"),
                "published": published,
                "audio_url": audio_url,
                "audio_type": audio_type or "audio/mpeg",
                "duration": entry.get("itunes_duration"),
                "summary": Truncator(unescape(summary)).chars(220),
                "image": image,
            })
            if len(episodes) >= MAX_RSS_EPISODES:
                break

        feed_info = feed.feed
        feed_image = None
        if feed_info.get("image") and feed_info["image"].get("href"):
            feed_image = feed_info["image"]["href"]

        return {
            "title": feed_info.get("title"),
            "author": feed_info.get("author") or feed_info.get("itunes_author"),
            "link": feed_info.get("link"),
            "subtitle": strip_tags(feed_info.get("subtitle") or ""),
            "thumbnail": feed_image,
            "episodes": episodes,
        }

    def get_details(self, use_cache=True):
        """
        Platform details fetched from the network, cached for `refresh_interval_minutes`.
        Platforms embedding a live player need no network call and return an empty dict.
        """
        if self.platform == AudioPlatform.SOUNDCLOUD:
            fetcher = self.fetch_soundcloud_details
        elif self.platform == AudioPlatform.RSS:
            fetcher = self.fetch_rss_details
        else:
            return {}

        if not use_cache or not self.pk:
            return fetcher()

        key = self.get_cache_key()
        details = cache.get(key)
        if details is None:
            details = fetcher()
            # Only cache successful fetches so failures are retried on the next request
            if details:
                cache.set(key, details, self.get_cache_timeout())
        return details

    def get_embed_context(self, use_cache=True):
        """
        Everything the player template needs. Returns None when the playlist cannot be rendered.
        """
        details = self.get_details(use_cache=use_cache) or {}

        context = {
            "playlist": self,
            "platform": self.platform,
            "platform_label": self.platform_label,
            "details": details,
            "embed_url": None,
            "embed_height": self.embed_height,
            "episodes": details.get("episodes") or [],
        }

        if self.is_rss:
            if not context["episodes"]:
                return None
            return context

        context["embed_url"] = self.get_embed_url(soundcloud_resource_url=details.get("resource_url"))
        if not context["embed_url"]:
            return None
        return context


class AudioPlaylistEditView(EditView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        playlist = context.get("object")
        embed_context = None
        if playlist:
            try:
                embed_context = playlist.get_embed_context()
            except Exception as e:
                logger.warning("Could not build audio playlist preview: %s", e)
        context["embed_context"] = embed_context
        return context


class AudioPlaylistViewSet(SnippetViewSet):
    model = AudioPlaylist
    icon = "media"
    list_display = ["title", "platform", "playlist_url"]
    list_filter = ["platform"]
    search_fields = ["title", "playlist_url"]
    edit_view_class = AudioPlaylistEditView
    edit_template_name = "audio/playlist_edit.html"


register_snippet(AudioPlaylistViewSet)
