from geomanager.models import AbstractStationsPage
from wagtail.models import Page

from base.mixins import MetadataPageMixin


class StationsPage(MetadataPageMixin, AbstractStationsPage):
    template = "stations/stations_list_page.html"
    parent_page_types = ["home.HomePage"]
    subpage_types = []
    max_count = 1

    content_panels = Page.content_panels
