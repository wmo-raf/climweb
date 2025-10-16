from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.models import Page
from wagtailmailchimp.models import AbstractMailChimpPage
from wagtailmautic.models import BaseMauticFormPage

from climweb.base.mixins import MetadataPageMixin
from climweb.base.seo_utils import get_homepage_meta_image, get_homepage_meta_description


class MauticMailingListSubscriptionPage(MetadataPageMixin, BaseMauticFormPage, Page):
    template = 'mailing_list_subscription.html'
    parent_page_types = ['home.HomePage']
    subpage_types = []
    max_count = 1
    
    # don't cache this page because it has a form
    cache_control = 'no-cache'
    
    heading = models.CharField(max_length=255, blank=True, null=True, help_text=_("Heading"), verbose_name=_("Heading"))
    introduction_text = models.TextField(blank=True, null=True, verbose_name=_("Introduction text"))
    
    content_panels = Page.content_panels + [
        FieldPanel('heading'),
        FieldPanel('introduction_text'),
    ] + BaseMauticFormPage.content_panels
    
    def get_meta_image(self):
        meta_image = super().get_meta_image()
        
        if not meta_image:
            meta_image = get_homepage_meta_image(self.get_site())
        
        return meta_image
    
    def get_meta_description(self):
        meta_description = super().get_meta_description()
        
        if not meta_description:
            meta_description = get_homepage_meta_description(self.get_site())
        
        return meta_description
    
    def save(self, *args, **kwargs):
        if self.introduction_text:
            self.search_description = self.introduction_text
        
        super(MauticMailingListSubscriptionPage, self).save(*args, **kwargs)


class MailchimpMailingListSubscriptionPage(MetadataPageMixin, AbstractMailChimpPage, Page):
    template = 'mailing_list_subscription.html'
    parent_page_types = ['home.HomePage']
    subpage_types = []
    max_count = 1
    
    # don't cache this page because it has a form
    cache_control = 'no-cache'
    
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
