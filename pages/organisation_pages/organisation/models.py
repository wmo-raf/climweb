from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.models import Page

from base.mixins import MetadataPageMixin


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
