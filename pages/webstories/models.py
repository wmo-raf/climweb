from wagtail.models import Page
from wagtail_webstories_editor.models import AbstractWebStoryListPage, WebStory

from base.mixins import MetadataPageMixin


class WebStoryListPage(MetadataPageMixin, AbstractWebStoryListPage):

    content_panels = Page.content_panels + [

    ]


    @property
    def web_stories(self):
        live_stories = WebStory.objects.live().order_by("created_at")
        return live_stories
