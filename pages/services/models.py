from django.db import models
from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import (FieldPanel, MultiFieldPanel, PageChooserPanel, InlinePanel)
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page, Orderable
from wagtailmetadata.models import MetadataPageMixin

from base import blocks
from base.models import ServiceCategory, AbstractBannerWithIntroPage
from nmhs_cms.settings.base import SUMMARY_RICHTEXT_FEATURES
from pages.events.models import EventPage
from pages.news.models import NewsPage
from pages.organisation_pages.projects.models import ServiceProject
from pages.products.models import ProductPage
from pages.publications.models import PublicationPage
from pages.videos.models import YoutubePlaylist


class ServiceIndexPage(MetadataPageMixin, Page):
    parent_page_types = ['home.HomePage']
    subpage_types = ['services.ServicePage']
    template = "subpages_listing.html"

    listing_heading = models.CharField(max_length=255, default="Explore our Services",
                                       verbose_name=_("Services listing Heading"))
    max_count = 1

    content_panels = Page.content_panels + [
        FieldPanel("listing_heading")
    ]

    def get_children_pages(self):
        return self.get_children().live()

    class Meta:
        verbose_name = _('Service List Page')
        verbose_name_plural = _('Service List Pages')


class ServicePage(AbstractBannerWithIntroPage):
    template = 'services/service_page.html'
    parent_page_types = ['services.ServiceIndexPage']
    subpage_types = ['flex_page.FlexPage',]
    show_in_menus_default = True

    service = models.OneToOneField(ServiceCategory, on_delete=models.PROTECT, verbose_name=_("Service"))

    what_we_do_items = StreamField([
        ('what_we_do', blocks.WhatWeDoBlock()),
    ], null=True, blank=True, use_json_field=True)

    what_we_do_button_text = models.TextField(max_length=20, blank=True, null=True,
                                              verbose_name=_("What we do button text"))
    what_we_do_button_link = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("What we do button link")
    )

    projects_description = RichTextField(help_text=_("Projects description text"), blank=True, null=True,
                                         features=SUMMARY_RICHTEXT_FEATURES, verbose_name=_("Project Description"))

    feature_block_items = StreamField([
        ('feature_item', blocks.FeatureBlock()),
    ], null=True, blank=True, use_json_field=True, verbose_name=_("Feature block items"))

    youtube_playlist = models.ForeignKey(
        YoutubePlaylist,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Youtube playlist")
    )

    content_panels = Page.content_panels + [
        FieldPanel('service'),
        *AbstractBannerWithIntroPage.content_panels,
        MultiFieldPanel([
            FieldPanel('what_we_do_items'),
            FieldPanel('what_we_do_button_text'),
            PageChooserPanel('what_we_do_button_link'),
        ],
            heading=_("What we do in this Service section"),
        ),
        MultiFieldPanel([
            FieldPanel('projects_description'),
        ],
            heading=_("Projects Section"),
        ),
        FieldPanel('feature_block_items'),
        FieldPanel('youtube_playlist'),
        InlinePanel('applications', heading=_("Applications"), label=_("Heading")),
    ]

    class Meta:
        verbose_name = _('Service Page')
        verbose_name_plural = _('Service Pages')

    @cached_property
    def products(self):
        """
        Get list of products related to this service
        :return: products list
        """
        # Get all products related to this service
        products = ProductPage.objects.filter(Q(service=self.service) | Q(other_services__in=[self.service]))

        return products

    @cached_property
    def listing_image(self):
        if self.banner_image:
            return self.banner_image
        if self.introduction_image:
            return self.introduction_image
        return None

    @cached_property
    def projects(self):
        """
        Get list of projects related to this service
        :return: projects list
        """
        # Get all projects related to this service
        projects = ServiceProject.objects.filter(service=self.service, project__live=True)
        return projects

    @cached_property
    def events(self):
        """
        Get list of events related to this service and not archived
        :return: events list
        """
        events = EventPage.objects.live().filter(
            category__in=[self.service], is_archived=False, is_hidden=False).order_by('-date_from')[:3]

        return events

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

    @cached_property
    def nav_menu_icon(self):
        return self.service.icon

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        if self.youtube_playlist:
            context['youtube_playlist_url'] = self.youtube_playlist.get_playlist_items_api_url(request)

        return context


class ServiceApplication(Orderable):
    page = ParentalKey(ServicePage, on_delete=models.CASCADE, related_name="applications")
    application = models.ForeignKey("base.Application", on_delete=models.CASCADE, verbose_name=_("Application"))
