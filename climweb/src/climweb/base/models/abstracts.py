from django.db import models
from django.template.defaultfilters import truncatechars
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import MultiFieldPanel, FieldPanel, PageChooserPanel
from wagtail.fields import RichTextField
from wagtail.models import Page

from climweb.base.mixins import MetadataPageMixin
from climweb.base.utils import get_first_non_empty_p_string
from climweb.config.settings.base import SUMMARY_RICHTEXT_FEATURES


class AbstractBannerPage(MetadataPageMixin, Page):
    class Meta:
        abstract = True
    
    banner_image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name=_("Banner Image"),
        help_text=_("A high quality banner image"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    banner_title = models.CharField(max_length=255, verbose_name=_('Banner Title'))
    banner_subtitle = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Banner Subtitle'))
    call_to_action_button_text = models.CharField(max_length=100, blank=True, null=True,
                                                  verbose_name=_('Call to action button text'))
    call_to_action_related_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_('Call to action related page')
    )
    
    content_panels = [
        MultiFieldPanel(
            [
                FieldPanel('banner_image'),
                FieldPanel('banner_title'),
                FieldPanel('banner_subtitle'),
                FieldPanel('call_to_action_button_text'),
                PageChooserPanel('call_to_action_related_page')
            ],
            heading=_("Banner Section"),
        )
    ]
    
    def get_meta_image(self):
        meta_image = super().get_meta_image()
        
        if not meta_image:
            meta_image = self.banner_image
        
        if not meta_image:
            meta_image = self.get_parent().specific.get_meta_image()
        
        return meta_image
    
    def get_meta_description(self):
        meta_description = super().get_meta_description()
        
        if not meta_description and self.banner_subtitle:
            meta_description = self.banner_subtitle
        
        # use banner title as last resort
        if not meta_description:
            meta_description = self.banner_title
        
        return meta_description


class AbstractIntroPage(MetadataPageMixin, Page):
    introduction_title = models.CharField(max_length=100, verbose_name=_('Introduction Title'),
                                          help_text=_("Introduction section title"), )
    introduction_text = RichTextField(features=SUMMARY_RICHTEXT_FEATURES, verbose_name=_('Introduction text'),
                                      help_text=_("Introduction section description"))
    introduction_image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name=_("Introduction Image"),
        help_text=_("A high quality image"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    
    introduction_button_text = models.CharField(max_length=20, blank=True, null=True,
                                                verbose_name=_("Introduction button text"), )
    introduction_button_link = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Introduction button link"),
    )
    
    introduction_button_link_external = models.URLField(max_length=200, blank=True, null=True,
                                                        help_text="External Link if applicable. Ignored if internal "
                                                                  "page above is chosen")
    
    class Meta:
        abstract = True
    
    content_panels = [
        MultiFieldPanel(
            [
                FieldPanel('introduction_title'),
                FieldPanel('introduction_image'),
                FieldPanel('introduction_text'),
                FieldPanel('introduction_button_text'),
                PageChooserPanel('introduction_button_link'),
                PageChooserPanel('introduction_button_link_external'),
            ],
            heading=_("Introduction Section"),
        ),
    ]
    
    def get_meta_image(self):
        meta_image = super().get_meta_image()
        
        if not meta_image and self.introduction_image:
            meta_image = self.introduction_image
        
        return meta_image
    
    def get_meta_description(self):
        meta_description = super().get_meta_description()
        
        if not meta_description and self.introduction_text:
            p = get_first_non_empty_p_string(self.introduction_text)
            if p:
                # Limit the search meta desc to google's 160 recommended chars
                meta_description = truncatechars(p, 160)
        
        # use introduction_title as last resort
        if not meta_description:
            meta_description = self.introduction_title
        
        return meta_description


class AbstractBannerWithIntroPage(AbstractBannerPage, AbstractIntroPage):
    class Meta:
        abstract = True
    
    content_panels = [
        *AbstractBannerPage.content_panels,
        *AbstractIntroPage.content_panels,
    ]
