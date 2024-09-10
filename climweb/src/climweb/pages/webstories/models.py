from wagtail.models import Page
from wagtail_webstories_editor.models import AbstractWebStoryListPage

from climweb.base.mixins import MetadataPageMixin


class WebStoryListPage(MetadataPageMixin, AbstractWebStoryListPage):
    template = "webstories/webstory_list_page.html"
    parent_page_types = ["home.HomePage"]
    subpage_types = []
    max_count = 1

    content_panels = Page.content_panels + [

    ]

    @property
    def web_stories(self):
        live_stories = self.live_stories.order_by("created_at")

        for story in live_stories:
            featured_media = story.config.get("featuredMedia")

        return live_stories
