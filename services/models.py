from django.db import models
from django.template.defaultfilters import truncatechars
from django.utils.functional import cached_property
from wagtail.admin.panels import (FieldPanel, MultiFieldPanel, PageChooserPanel)
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page

from core import blocks
from core.models import ServiceCategory, ServiceApplication
from core.utils import get_first_non_empty_p_string
from nmhs_cms.settings.base import SUMMARY_RICHTEXT_FEATURES
from media_pages.news.models import NewsPage
from media_pages.publications.models import PublicationPage
from media_pages.videos.models import YoutubePlaylist
# from organisation_pages.events.models import EventPage
from organisation_pages.projects.models import ServiceProject

class ServicesPage(Page):

    parent_page_types = ['home.HomePage']
    subpage_types = ['services.ServiceIndexPage']

    max_count = 1

    class Meta:
        verbose_name = 'Service Page'
        verbose_name_plural = 'Service Pages'

class ServiceIndexPage(Page):
    template = 'services_page.html'
    parent_page_types = ['services.ServicesPage']
    subpage_types = []
    show_in_menus_default = True

    service = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT, null=True)

    banner_image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name="Banner Image",
        help_text="A high quality image related to this Service",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    banner_title = models.CharField(max_length=255, null=True)
    banner_subtitle = models.CharField(max_length=255, null=True)

    call_to_action_button_text = models.CharField(max_length=100, blank=True, null=True)
    call_to_action_related_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    call_to_action_external_link = models.URLField(max_length=200, blank=True, null=True,
                                                   help_text="External Link if applicable")

    introduction_title = models.CharField(max_length=100, help_text="Introduction section title", null=True)
    introduction_text = RichTextField(help_text="A description of what ORG does under  this Service",
                                      features=SUMMARY_RICHTEXT_FEATURES, null=True)
    introduction_image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name="Introduction Image",
        help_text="A high quality image related to this Service",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    introduction_button_text = models.TextField(max_length=20, blank=True, null=True)
    introduction_button_link = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    introduction_button_link_external = models.URLField(max_length=200, blank=True, null=True,
                                                        help_text="External Link if applicable. Ignored if internal "
                                                                  "page above is chosen")

    # TODO: FIX THIS AND RETURN
    # what_we_do_items = StreamField([
    #     ('what_we_do', blocks.WhatWeDoBlock()),
    # ], null=True, blank=True,  use_json_field=False)
    what_we_do_button_text = models.TextField(max_length=20, blank=True, null=True)
    what_we_do_button_link = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    projects_description = RichTextField(help_text="Projects description text", blank=True, null=True,
                                         features=SUMMARY_RICHTEXT_FEATURES)

    feature_block_items = StreamField([
        ('feature_item', blocks.FeatureBlock()),
    ], null=True, blank=True,  use_json_field=True)
    youtube_playlist = models.ForeignKey(
        YoutubePlaylist,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    content_panels = Page.content_panels + [
        FieldPanel('service'),
        MultiFieldPanel(
            [
                FieldPanel('banner_image'),
                FieldPanel('banner_title'),
                FieldPanel('banner_subtitle'),
                FieldPanel('call_to_action_button_text'),
                PageChooserPanel('call_to_action_related_page', ),
                FieldPanel('call_to_action_external_link')

            ],
            heading="Banner Section",
        ),
        MultiFieldPanel(
            [
                FieldPanel('introduction_title'),
                FieldPanel('introduction_image'),
                FieldPanel('introduction_text'),
                FieldPanel('introduction_button_text'),
                PageChooserPanel('introduction_button_link'),
                FieldPanel('introduction_button_link_external')
            ],
            heading="Introduction Section",
        ),
        MultiFieldPanel([
            # FieldPanel('what_we_do_items'),
            FieldPanel('what_we_do_button_text'),
            PageChooserPanel('what_we_do_button_link'),
        ],
            heading="What we do in this Service section ",
        ),
        MultiFieldPanel([
            FieldPanel('projects_description'),
        ],
            heading="Projects Section",
        ),
        FieldPanel('feature_block_items'),
        FieldPanel('youtube_playlist'),
    ]

    @cached_property
    def projects(self):
        """
        Get list of projects related to this service
        :return: projects list
        """
        # Get all projects related to this service
        projects = ServiceProject.objects.filter(service=self.service, project__live=True)
        return projects

    # TODO: ADD EVENTS TO SERVICES PAGE 
    # @cached_property
    # def events(self):
    #     """
    #     Get list of events related to this service and not archived
    #     :return: events list
    #     """
    #     events = EventPage.objects.live().filter(
    #         category__in=[self.service], is_archived=False, is_hidden=False).order_by('-date_from')[:3]

    #     return events

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
    def applications(self):
        """
        Get all applications related to this service
        :return: application list
        """
        apps = ServiceApplication.objects.filter(service=self.service)
        return apps

    def save(self, *args, **kwargs):
        # if not self.search_image and self.banner_image:
        #     self.search_image = self.banner_image
        if not self.search_description and self.introduction_text:
            p = get_first_non_empty_p_string(self.introduction_text)
            if p:
                # Limit the search meta desc to google's 160 recommended chars
                self.search_description = truncatechars(p, 160)
        return super().save(*args, **kwargs)
