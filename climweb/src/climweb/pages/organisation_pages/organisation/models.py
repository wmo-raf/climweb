from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.models import Page

from climweb.base.mixins import MetadataPageMixin


class OrganisationIndexPage(MetadataPageMixin, Page):
    template = "subpages_listing.html"
    parent_page_types = ['home.HomePage']
    max_count = 1
    subpage_types = [
        'about.AboutPage',
        'partners.PartnersPage',
        'vacancies.VacanciesPage',
        'projects.ProjectIndexPage',
        'tenders.TendersPage',
        'staff.StaffPage',
        'flex_page.FlexPage',
    ]
    show_in_menus_default = True
    
    listing_heading = models.CharField(max_length=255, default="Explore our Organisation",
                                       verbose_name=_("Organisation listing Heading"))
    
    content_panels = Page.content_panels + [
        FieldPanel("listing_heading"),
    ]
    
    class Meta:
        verbose_name = _("Organisation Index Page")
    
    def get_meta_image(self):
        meta_image = super().get_meta_image()
        
        if not meta_image:
            home_page = self.get_parent().specific
            meta_image = home_page.get_meta_image()
        
        return meta_image
    
    def get_meta_description(self):
        meta_description = super().get_meta_description()
        
        if not meta_description:
            home_page = self.get_parent().specific
            meta_description = home_page.get_meta_description()
        
        return meta_description
