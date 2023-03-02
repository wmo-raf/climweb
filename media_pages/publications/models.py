from datetime import date, datetime

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.forms.widgets import CheckboxSelectMultiple
from django.template.defaultfilters import truncatechars
from django.utils.functional import cached_property
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalManyToManyField, ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import (FieldPanel, MultiFieldPanel,
                                         PageChooserPanel)
from wagtail.fields import RichTextField
from wagtail.api import APIField
from wagtail.models import Page
from wagtail.documents.models import Document

from core.models import PublicationType, ServiceCategory 
from core.utils import paginate, get_years, query_param_to_list, get_first_non_empty_p_string
from nmhs_cms.settings.base import SUMMARY_RICHTEXT_FEATURES


class PublicationsIndexPage(Page):
    template = 'publications_index_page.html'
    parent_page_types = ['home.HomePage']
    subpage_types = ['publications.PublicationPage']
    max_count = 1
    show_in_menus_default = True

    banner_image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name="Banner Image",
        help_text="A high quality image related to Publications",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    banner_title = models.CharField(max_length=255)
    banner_subtitle = models.CharField(max_length=255)

    call_to_action_button_text = models.CharField(max_length=100, blank=True, null=True)
    call_to_action_related_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    earliest_publication_year = models.PositiveIntegerField(
        default=datetime.now().year,
        validators=[
            MinValueValidator(2000),
            MaxValueValidator(datetime.now().year),
        ],
        help_text="The year for the earliest available publication. This is used to generate the years available for "
                  "filtering ")
    publications_per_page = models.PositiveIntegerField(default=6, validators=[
        MinValueValidator(6),
        MaxValueValidator(20),
    ], help_text="How many publications per page should be visible on the all publications section ?")

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel('banner_image'),
                FieldPanel('banner_title'),
                FieldPanel('banner_subtitle'),
                FieldPanel('call_to_action_button_text'),
                FieldPanel('call_to_action_related_page', )
            ],
            heading="Banner Section",
        ),
        MultiFieldPanel(
            [
                FieldPanel('publications_per_page'),
                FieldPanel('earliest_publication_year'),
            ],
            heading="Other Settings",
        ),
    ]

    @cached_property
    def filters(self):
        from organisation_pages.projects.models import ProjectPage
        publication_types = PublicationType.objects.all()
        service_categories = ServiceCategory.objects.all()
        projects = ProjectPage.objects.live()

        return {
            'publication_types': publication_types,
            'service_categories': service_categories,
            'year': get_years(self.earliest_publication_year),
            'projects': projects
        }

    def filter_publications(self, request):
        publications = self.all_publications

        years = query_param_to_list(request.GET.get("year"), as_int=True)
        publication_types = query_param_to_list(request.GET.get("publication_type"), as_int=True)
        services = query_param_to_list(request.GET.get("service"), as_int=True)
        q = request.GET.get('q')

        filters = models.Q()

        if years:
            filters &= models.Q(publication_date__year__in=years)
        if publication_types:
            filters &= models.Q(publication_type__in=publication_types)
        if services:
            filters &= models.Q(categories__in=services)

        if q:
            filters &= models.Q(title__icontains=q)

        return publications.filter(filters).distinct()

    def filter_and_paginate_events(self, request):
        page = request.GET.get('page')

        filtered_publications = self.filter_publications(request)
        paginated_publications = paginate(filtered_publications, page, self.publications_per_page)

        return paginated_publications

    @cached_property
    def featured_publications(self):
        return PublicationPage.objects.live().filter(featured=True).order_by('-publication_date')[:4]

    @cached_property
    def all_publications(self):
        return PublicationPage.objects.live().order_by('-publication_date')

    def get_context(self, request, *args, **kwargs):
        context = super(PublicationsIndexPage, self).get_context(
            request, *args, **kwargs)

        context['publications'] = self.filter_and_paginate_events(request)

        return context

    def save(self, *args, **kwargs):
        # if not self.search_image and self.thumbnail: TODO: Search Image SEO Fix
        #     self.search_image = self.thumbnail
        if not self.search_description and self.banner_subtitle:
            # Limit the search meta desc to google's 160 recommended chars
            self.search_description = truncatechars(self.banner_subtitle, 160)
        return super().save(*args, **kwargs)

    
    


class PublicationPageTag(TaggedItemBase):
    content_object = ParentalKey('publications.PublicationPage', on_delete=models.CASCADE,
                                 related_name='publications_tags',)


class PublicationPage(Page):
    template = 'publication_page.html'
    parent_page_types = ['publications.PublicationsIndexPage']
    subpage_types = []

    publication_type = models.ForeignKey('core.PublicationType', on_delete=models.PROTECT)
    categories = ParentalManyToManyField('core.ServiceCategory', verbose_name="Services related to this publication")
    projects = ParentalManyToManyField('projects.ProjectPage', blank=True, verbose_name="Relevant Projects")
    summary = RichTextField(features=SUMMARY_RICHTEXT_FEATURES)
    publication_date = models.DateField("Date of Publish", default=date.today)
    is_visible_on_homepage = models.BooleanField(default=False,
                                                 help_text="Should this appear in the homepage as"
                                                           " an alert/latest update ?")
    featured = models.BooleanField(
        "Mark as featured", default=False, help_text="Featured publications appear on the publications landing page")
    period_start_date = models.DateField(blank=True, null=True,
                                         help_text="Optional start date for which this publication is relevant")
    period_end_date = models.DateField(blank=True, null=True,
                                       help_text="Optional end date for which this publication is relevant")
    peer_reviewed = models.BooleanField(default=False, help_text="Is this a peer reviewed publication ?")

    thumbnail = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Publication image",
        help_text="This can be a screenshot of the front page of the publication"
    )
    document = models.ForeignKey(
        'core.CustomDocumentModel',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='+',
        verbose_name="Document or File",
        help_text="Here you can upload pdfs, word documents, powerpoints, zip files or any other file"
    )
    external_publication_url = models.URLField(max_length=500, blank=True, null=True,
                                               verbose_name="External Url - *Only If published/hosted somewhere else",
                                               help_text="Link to published resource if external")

    tags = ClusterTaggableManager(through=PublicationPageTag, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('publication_type'),
        FieldPanel('categories', widget=CheckboxSelectMultiple),
        FieldPanel('projects', widget=CheckboxSelectMultiple),
        FieldPanel('thumbnail'),
        FieldPanel('publication_date'),
        FieldPanel('document'),
        FieldPanel('external_publication_url'),
        FieldPanel('summary'),
        FieldPanel('featured'),
        FieldPanel('is_visible_on_homepage'),
        FieldPanel('peer_reviewed'),
        MultiFieldPanel([
            FieldPanel('period_start_date'),
            FieldPanel('period_end_date'),
        ], heading="Additional Details"),
    ]

    api_fields = [
        APIField('publication_type'),
        APIField('categories'),
        APIField('projects'),
        APIField('thumbnail'),
        APIField('publication_date'),
        APIField('document'),
        APIField('summary'),
    ]

    @cached_property
    def publication_title(self):
        return self.title

    @cached_property
    def related_items(self):
        related_items = PublicationPage.objects.live().exclude(pk=self.pk).order_by('-publication_date')[:3]
        return related_items

    @cached_property
    def card_props(self):
        card_file = None

        if self.document:
            card_file = {
                "size": self.document.file_size,
                "url": self.document.url,
                "downloads": self.document.download_count
            }

        card_tags = self.tags.all()

        props = {
            "card_image": self.thumbnail,
            "card_title": self.publication_title,
            "card_tag_category": self.publication_type.name,
            "card_text": self.summary,
            "card_meta": self.publication_date,
            "card_more_link": self.url,
            "card_tag": "Publication",
            "card_file": card_file,
            "card_external_publication_url": self.external_publication_url,
            "card_tags": card_tags,
            # "card_views": self.webhits.count,
            "card_ga_label": "Publication",
        }

        return props

    def get_context(self, request, *args, **kwargs):
        context = super(PublicationPage, self).get_context(request, *args, **kwargs)

        context['related_items'] = self.related_items

        return context

    class Meta:
        verbose_name = "Publication"

    def save(self, *args, **kwargs):
        # if not self.search_image and self.thumbnail: TODO: Search Image SEO Fix
        #     self.search_image = self.thumbnail
        if not self.search_description and self.summary:
            p = get_first_non_empty_p_string(self.summary)
            if p:
                # Limit the search meta desc to google's 160 recommended chars
                self.search_description = truncatechars(p, 160)
        return super().save(*args, **kwargs)

    