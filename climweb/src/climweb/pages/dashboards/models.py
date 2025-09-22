from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField
from django.db import models
from wagtail_color_panel.edit_handlers import NativeColorPanel
from climweb.pages.dashboards.blocks import DashboardSectionBlock
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import truncatechars
from climweb.base.mixins import MetadataPageMixin
from django.utils.html import strip_tags


class DashboardGalleryPage(Page):
    subpage_types = ['dashboards.DashboardPage']  # only allow DashboardPage children
    parent_page_types = ['home.HomePage']

    description = models.CharField(max_length=255, null=True)
    max_count = 1  # optional: only one index page site-wide

    content_panels = Page.content_panels + [
        FieldPanel("description"),
    ]
    class Meta:
        verbose_name = "Dashboards Gallery / Atlas"

class DashboardPage(MetadataPageMixin, Page):
    template = 'dashboards/dashboard_page.html'
    parent_page_types = ['dashboards.DashboardGalleryPage']
    banner_title = models.CharField(max_length=255)
    banner_description = RichTextField(help_text=_("Banner description"))
    banner_background_color = models.CharField(
        max_length=7,
        default="#f5f5f5",
        help_text=_("Hex color code for banner background (e.g., #ffffff)")
    )
    banner_image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name=_("Banner Image"),
        help_text=_("A high quality banner image"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    body = StreamField([
        ("section", DashboardSectionBlock()),
    ], use_json_field=True)

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("banner_title"),
            FieldPanel("banner_description"),
            NativeColorPanel("banner_background_color"),
            FieldPanel("banner_image"),
        ], heading="Banner Settings"),
        FieldPanel("body"),
    ]

    def get_meta_image(self):
        if self.search_image:
            return self.search_image
        return self.banner_image
    
    def save(self, *args, **kwargs):
        if not self.search_image and self.banner_image:
            self.search_image = self.banner_image
        
        if not self.seo_title and self.banner_title:
            self.seo_title = self.banner_title
        
        if not self.search_description and self.banner_description:
            plain_text_description = strip_tags(self.banner_description)
            self.search_description = truncatechars(plain_text_description, 160)

        
        return super().save(*args, **kwargs)
    
    def get_meta_description(self):
        if self.search_description:
            return self.search_description
        return strip_tags(self.banner_description)
    
    def get_meta_title(self):
        if self.seo_title:
            return self.seo_title
        return self.banner_title

    class Meta:
        verbose_name = "Dashboard Page"


