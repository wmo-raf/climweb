from django.utils.translation import gettext_lazy as _
from wagtail.models import Page

from base.mixins import MetadataPageMixin


class OrganisationIndexPage(MetadataPageMixin, Page):
    parent_page_types = ['home.HomePage']
    max_count = 1
    subpage_types = [
        'about.AboutPage',
        'partners.PartnersPage',
        'vacancies.VacanciesPage',
        'projects.ProjectIndexPage',
        'tenders.TendersPage'
    ]
    show_in_menus_default = True

    class Meta:
        verbose_name = _("About Index Page")
