from django.db import models
from django.utils.functional import cached_property
from wagtail.models import Page
from django.urls import reverse

from capeditor.models import AbstractCapAlertPage

# Create your models here.
class CapAlertPage(AbstractCapAlertPage):
    template = "capeditor/alert_detail.html"

    parent_page_types = ["home.HomePage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        *AbstractCapAlertPage.content_panels
    ]

    @cached_property
    def xml_link(self):
        return reverse("cap_alert_detail", args=(self.identifier,))