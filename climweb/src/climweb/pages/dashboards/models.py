from climweb.base.blocks import CategorizedAdditionalMaterialBlock
from climweb.base.models.snippets import ServiceCategory
from climweb.pages.news.models import NewsPage
from climweb.pages.publications.models import PublicationPage
from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField
from django.db import models
from django.utils.functional import cached_property
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
        verbose_name =  _("Dashboards Gallery / Atlas")

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

    service = models.OneToOneField(ServiceCategory, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Service"), help_text=_("The service this dashboard is associated with. This is useful in fetching the latest updates i.e publications, news, articles related to this service."))

    body = StreamField([
        ("section", DashboardSectionBlock()),
    ], use_json_field=True)

    additional_materials = StreamField([
        ('material', CategorizedAdditionalMaterialBlock())
    ], null=True, blank=True, use_json_field=True, verbose_name=_("Additional Materials"))

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("banner_title"),
            FieldPanel("banner_description"),
            NativeColorPanel("banner_background_color"),
            FieldPanel("banner_image"),
        ], heading="Banner Settings"),
        FieldPanel('service'),
        FieldPanel("body"),
        FieldPanel("additional_materials"),
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
    

    @cached_property
    def latest_updates(self):
        updates = []
        
        news = NewsPage.objects.live().filter(services__in=[self.service]).order_by('-is_featured', '-date')[:2]
        
        publications = PublicationPage.objects.live().filter(categories__in=[self.service]).order_by(
            '-featured',
            '-publication_date')
        
        if news.exists():
            if news.count() > 1:
                # we have 2 news , get 2 publications
                publications = publications[:2]
            else:
                # we have 1 news, get 3 publications
                publications = publications[:3]
            # add news
            updates.extend(news)
        else:
            # no news, get 4 publications
            publications = publications[:4]
        
        # add publications
        updates.extend(publications)
        
        return updates

    class Meta:
        verbose_name = "Dashboard Page"


