from django.db import models
from django.template.defaultfilters import truncatechars
from django.utils.functional import cached_property
from wagtail.admin.panels import MultiFieldPanel, FieldPanel, PageChooserPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page

from cms_pages.webicons.edit_handlers import WebIconChooserPanel
from core import blocks
from core.utils import get_first_non_empty_p_string
from nmhs_cms.settings.base import SUMMARY_RICHTEXT_FEATURES
from media_pages.news.models import NewsPage
from media_pages.videos.models import YoutubePlaylist


class MediaIndexPage(Page):
    template = 'mediacenter_index.html'
    parent_page_types = ['home.HomePage']
    subpage_types = []
    max_count = 1

    banner_image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name="Banner Image",
        help_text="A high quality image related to IFRAH",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    banner_title = models.CharField(max_length=255)
    banner_subtitle = models.CharField(max_length=255, blank=True, null=True)

    call_to_action_button_text = models.CharField(max_length=100, blank=True, null=True)
    call_to_action_related_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    call_to_action_external_link = models.URLField(max_length=200, blank=True, null=True,
                                                   help_text="External Link if applicable")

    introduction_title = models.CharField(max_length=100, help_text="Introduction section title")
    introduction_text = RichTextField(features=SUMMARY_RICHTEXT_FEATURES)

    introduction_image = models.ForeignKey(
        'webicons.WebIcon',
        verbose_name="Media SVG Illustration",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    introduction_button_text = models.TextField(max_length=20, blank=True, null=True)
    introduction_button_link = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    introduction_button_link_external = models.URLField(max_length=200, blank=True, null=True,
                                                        help_text="External Link if applicable. Ignored if internal "
                                                                  "page above is chosen")

    feature_block_items = StreamField(
        [
            ('feature_item', blocks.FeatureBlock()),
        ],
        null=True, blank=True, verbose_name="Items", use_json_field=True)

    youtube_playlist = models.ForeignKey(
        YoutubePlaylist,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel('banner_image'),
                FieldPanel('banner_title'),
                FieldPanel('banner_subtitle'),
                FieldPanel('call_to_action_button_text'),
                PageChooserPanel('call_to_action_related_page'),
                FieldPanel('call_to_action_external_link')
            ],
            heading="Banner Section",
        ),
        MultiFieldPanel(
            [
                FieldPanel('introduction_title'),
                WebIconChooserPanel('introduction_image'),
                FieldPanel('introduction_text'),
                FieldPanel('introduction_button_text'),
                PageChooserPanel('introduction_button_link'),
                FieldPanel('introduction_button_link_external')
            ],
            heading="Introduction Section",
        ),
        FieldPanel('feature_block_items'),
        FieldPanel('youtube_playlist'),
    ]

    @cached_property
    def latest_news(self):

        return NewsPage.objects.live().order_by('-is_featured', '-date')[:4]

    def save(self, *args, **kwargs):
        # if not self.search_image and self.banner_image:
        #     self.search_image = self.banner_image
        if not self.search_description and self.introduction_text:
            p = get_first_non_empty_p_string(self.introduction_text)
            if p:
                # Limit the search meta desc to google's 160 recommended chars
                self.search_description = truncatechars(p, 160)
        return super().save(*args, **kwargs)