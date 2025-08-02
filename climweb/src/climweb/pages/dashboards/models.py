from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField
from django.db import models
from wagtail_color_panel.edit_handlers import NativeColorPanel
from climweb.pages.dashboards.blocks import DashboardSectionBlock

class DashboardGalleryPage(Page):
    subpage_types = ['dashboards.DashboardPage']  # only allow DashboardPage children
    parent_page_types = ['home.HomePage']

    description = models.CharField(max_length=255, null=True)
    max_count = 1  # optional: only one index page site-wide

    content_panels = Page.content_panels + [
        FieldPanel("description"),
    ]
    class Meta:
        verbose_name = "Dashboards Gallery"

class DashboardPage(Page):
    template = 'dashboards/dashboard_page.html'
    parent_page_types = ['dashboards.DashboardGalleryPage']
    banner_title = models.CharField(max_length=255)
    banner_description = RichTextField(help_text="Banner description")
    banner_background_color = models.CharField(
        max_length=7,
        default="#f5f5f5",
        help_text="Hex color code for banner background (e.g., #ffffff)"
    )

    body = StreamField([
        ("section", DashboardSectionBlock()),
    ], use_json_field=True)

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("banner_title"),
            FieldPanel("banner_description"),
            NativeColorPanel("banner_background_color"),
        ], heading="Banner Settings"),
        FieldPanel("body"),
    ]

    class Meta:
        verbose_name = "Dashboard Page"

