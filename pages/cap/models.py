from capeditor.models import AbstractCapAlertPage
from django.urls import reverse
from django.utils.functional import cached_property
from wagtail.models import Page

from wagtailmetadata.models import MetadataPageMixin


class CapAlertPage(MetadataPageMixin, AbstractCapAlertPage):
    template = "capeditor/alert_detail.html"

    parent_page_types = ["home.HomePage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        *AbstractCapAlertPage.content_panels
    ]

    @cached_property
    def xml_link(self):
        return reverse("cap_alert_detail", args=(self.identifier,))
