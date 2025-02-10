from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, PageChooserPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page

from climweb.base import blocks
from climweb.base.models import AbstractIntroPage
from climweb.config.settings.base import SUMMARY_RICHTEXT_FEATURES
from climweb.pages.organisation_pages.partners.models import Partner
from .blocks import TimelineBlock


class AboutPage(AbstractIntroPage):
    template = 'about_page.html'
    parent_page_types = ['organisation.OrganisationIndexPage']
    subpage_types = ['flex_page.FlexPage', ]
    max_count = 1
    show_in_menus_default = True
    
    mission = models.CharField(max_length=500, help_text=_("Organisation's mission"), blank=True, null=True,
                               verbose_name=_("Organisation's mission"))
    vision = models.CharField(max_length=500, help_text=_("Organisation's vision"), blank=True, null=True,
                              verbose_name=_("Organisation's vision"))
    
    timeline_heading = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Timeline Heading"))
    
    timeline = StreamField([
        ('nmhs_timeline', TimelineBlock()),
    ], null=True, blank=True, verbose_name=_("Timeline items"), use_json_field=True)
    
    org_struct_heading = models.CharField(max_length=250, help_text=_("Organisation's Structure Section Heading"),
                                          blank=True, null=True, verbose_name=_("Organisation's Struture Heading"),
                                          default="Our Organisational Structure")
    org_struct_description = RichTextField(help_text=_("Organisation's Structure Description"), blank=True, null=True,
                                           verbose_name=_("Organisation's Struture Description"),
                                           features=SUMMARY_RICHTEXT_FEATURES)
    org_struct_img = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name=_("Organisational Structure Image"),
        help_text=_("A high quality image related to your organisation's structure"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    
    feature_block = StreamField([
        ('feature_item', blocks.FeatureBlock()),
    ], null=True, blank=True, use_json_field=True, verbose_name=_("Feature Block"))
    
    additional_materials = StreamField([
        ('material', blocks.CategorizedAdditionalMaterialBlock())
    ], null=True, blank=True, use_json_field=True, verbose_name=_("Additional Materials"))
    
    accordion = StreamField(
        [
            ("accordion", blocks.AccordionBlock()),
        ],
        null=True,
        blank=True,
        use_json_field=True,
        verbose_name=_("Accordion"),
    )
    
    bottom_call_to_action_heading = models.CharField(max_length=100, blank=True, null=True,
                                                     verbose_name=_("Bottom Call to action heading"))
    bottom_call_to_action_description = models.TextField(blank=True, null=True,
                                                         verbose_name=_("Bottom call to action description"))
    bottom_call_to_action_button_text = models.CharField(max_length=20, blank=True, null=True,
                                                         verbose_name=_("Bottom call to action button text"))
    bottom_call_to_action_button_link = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Bottom call to action button link")
    )
    
    content_panels = Page.content_panels + [
        *AbstractIntroPage.content_panels,
        MultiFieldPanel(
            [
                FieldPanel('mission'),
                FieldPanel('vision'),
            ],
            heading=_("Mission & Vision Section"),
        ),
        MultiFieldPanel(
            [
                FieldPanel('org_struct_heading'),
                FieldPanel('org_struct_description'),
                FieldPanel('org_struct_img'),
            ],
            heading=_("Organisation Structure Section"),
        ),
        MultiFieldPanel([
            FieldPanel('timeline_heading'),
            FieldPanel('timeline'),
        ], heading="Historical Timeline Section"),
        FieldPanel('additional_materials'),
        FieldPanel('feature_block'),
        FieldPanel('accordion'),
        MultiFieldPanel(
            [
                FieldPanel('bottom_call_to_action_heading'),
                FieldPanel('bottom_call_to_action_description'),
                FieldPanel('bottom_call_to_action_button_text'),
                PageChooserPanel('bottom_call_to_action_button_link'),
            ],
            heading=_("Bottom Call to action Section"),
        ),
    ]
    
    class Meta:
        verbose_name = _("About Page")
    
    def get_meta_image(self):
        meta_image = super().get_meta_image()
        
        # get home page banner image as fallback
        if not meta_image:
            meta_image = self.get_parent().specific.get_meta_image()
        
        return meta_image
    
    @cached_property
    def listing_image(self):
        # if self.banner_image:
        #     return self.banner_image
        if self.introduction_image:
            return self.introduction_image
        return None
    
    @property
    def partners(self):
        return Partner.objects.filter(is_main=True)[:5]
