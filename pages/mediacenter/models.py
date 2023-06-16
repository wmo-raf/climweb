from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page

from base import blocks
from base.models import AbstractBannerWithIntroPage
from pages.news.models import NewsPage
from pages.videos.models import YoutubePlaylist


class MediaIndexPage(AbstractBannerWithIntroPage):
    template = 'mediacenter_index.html'
    parent_page_types = ['home.HomePage']
    subpage_types = []
    max_count = 1

    feature_block_items = StreamField(
        [
            ('feature_item', blocks.FeatureBlock()),
        ],
        null=True, blank=True, verbose_name=_("Items"), use_json_field=True)

    youtube_playlist = models.ForeignKey(
        YoutubePlaylist,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Youtube playlist")
    )

    content_panels = Page.content_panels + [
        *AbstractBannerWithIntroPage.content_panels,
        FieldPanel('feature_block_items'),
        FieldPanel('youtube_playlist'),
    ]

    class Meta:
        verbose_name = _("Media Page")

    @cached_property
    def latest_news(self):
        return NewsPage.objects.live().order_by('-is_featured', '-date')[:4]
