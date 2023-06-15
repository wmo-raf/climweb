from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.models import Page
from wagtailmailchimp.models import AbstractMailChimpPage
from wagtailmautic.models import BaseMauticFormPage

from base.mixins import MetadataPageMixin


class MauticMailingListSubscriptionPage(MetadataPageMixin, BaseMauticFormPage, Page):
    template = 'mailing_list_subscription.html'
    parent_page_types = ['home.HomePage']
    subpage_types = []
    max_count = 1

    heading = models.CharField(max_length=255, blank=True, null=True, help_text=_("Heading"), verbose_name=_("Heading"))
    introduction_text = models.TextField(blank=True, null=True, verbose_name=_("Introduction text"))

    content_panels = Page.content_panels + [
        FieldPanel('heading'),
        FieldPanel('introduction_text'),
    ] + BaseMauticFormPage.content_panels

    def save(self, *args, **kwargs):
        if self.introduction_text:
            self.search_description = self.introduction_text

        super(MauticMailingListSubscriptionPage, self).save(*args, **kwargs)


class MailchimpMailingListSubscriptionPage(MetadataPageMixin, AbstractMailChimpPage, Page):
    template = 'mailing_list_subscription.html'
    parent_page_types = ['home.HomePage']
    subpage_types = []
    max_count = 1

    heading = models.CharField(max_length=255, blank=True, null=True, help_text=_("Heading"), verbose_name=_("Heading"))
    introduction_text = models.TextField(blank=True, null=True, verbose_name=_("Introduction text"))

    content_panels = Page.content_panels + [
        FieldPanel('heading'),
        FieldPanel('introduction_text'),
    ] + AbstractMailChimpPage.content_panels

    def save(self, *args, **kwargs):
        if self.introduction_text:
            self.search_description = self.introduction_text

        super(MailchimpMailingListSubscriptionPage, self).save(*args, **kwargs)
