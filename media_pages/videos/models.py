import os

# from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from googleapiclient.discovery import build
from wagtail.admin.panels import (FieldPanel)
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page, Site
from wagtail.snippets.models import register_snippet

from core.models import ServiceCategory
from site_settings.models import IntegrationSettings


YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
youtube_service = None

# Youtube playlists
# @register_snippet
class YoutubePlaylist(models.Model):
    title = models.CharField(max_length=200, verbose_name=_("Title"))
    playlist_id = models.CharField(max_length=100,
                                   help_text=_("This is the playlist ID as obtained from Youtube. "
                                             "If the playlist is not created on Youtube, please create it first"),
                                             verbose_name=_("Playlist ID"))


    def set_api(self):
        try:
            current_site = Site.objects.get(is_default_site=True)

            # Get the SiteSettings for the current site
            settings = IntegrationSettings.for_site(current_site)
            api_key = settings.youtube_api
            YOUTUBE_API_KEY = api_key

            # creating Youtube Resource Object
            self.youtube_service = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                                    developerKey=YOUTUBE_API_KEY)

            return  self.youtube_service

        except Exception as e:
            print("Error: ",e)
            pass

    def __str__(self):
        return self.title


    @property
    def videos_count(self):
         # Get the current site
        youtube_service = self.set_api()

        if youtube_service:
            info = None
            try:
                videos = youtube_service.playlistItems().list(part="snippet",
                                                              playlistId=self.playlist_id).execute()

                if "pageInfo" in videos:
                    info = videos['pageInfo']['totalResults']
            except:
                pass
            return info
        return None

    def playlist_items(self, limit=None):
        youtube_service = self.set_api()

        if youtube_service:
            info = None
            try:
                videos = youtube_service.playlistItems().list(part="snippet,contentDetails",
                                                              playlistId=self.playlist_id,
                                                              maxResults=50).execute()
                
                if "items" in videos:
                    info = videos['items']
            except:
                pass

            # sort by video position in playlist 
            info.sort(key=lambda info_item:info_item['snippet']['position'], reverse=True)
            return info
        return None

    panels = [
        FieldPanel('title'),
        FieldPanel('playlist_id'),
    ]


class VideoGalleryPage(Page):
    template = 'video_index_page.html'
    parent_page_types = ['home.HomePage']
    subpage_types = []
    max_count = 1

    introduction = RichTextField(verbose_name=_("Introduction"))

    content_panels = Page.content_panels + [
        FieldPanel('introduction'),
    ]