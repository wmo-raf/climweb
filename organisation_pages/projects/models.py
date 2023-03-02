import calendar
from datetime import datetime

from dateutil import relativedelta
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.forms import CheckboxSelectMultiple
from django.template.defaultfilters import truncatechars
from django.utils.functional import cached_property
from modelcluster.fields import ParentalManyToManyField
from positions import PositionField
from rest_framework.fields import BooleanField
from wagtail.admin.panels import (FieldPanel, PageChooserPanel, MultiFieldPanel)
from wagtail.api import APIField
from wagtail.fields import StreamField, RichTextField
from wagtail.models import Orderable, Page

from core import blocks
from core.models import ServiceCategory
from core.utils import query_param_to_list, paginate, get_first_non_empty_p_string
from nmhs_cms.settings.base import SUMMARY_RICHTEXT_FEATURES
from media_pages.news.models import NewsPage
from media_pages.publications.models import PublicationPage
from media_pages.videos.models import YoutubePlaylist
from organisation_pages.events.models import EventPage


class ProjectIndexPage(Page):
    template = 'project_index_page.html'
    parent_page_types = ['home.HomePage']
    subpage_types = ['projects.ProjectPage']
    max_count = 1
    show_in_menus_default = True

    banner_image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name="Banner Image",
        help_text="A high quality image related to Projects",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    banner_title = models.CharField(max_length=255)
    banner_subtitle = models.CharField(max_length=255, blank=True, null=True)

    call_to_action_button_text = models.CharField(max_length=100, blank=True, null=True)
    call_to_action_related_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    introduction_title = models.CharField(max_length=100, help_text="Introduction section title")
    introduction_text = RichTextField(help_text="A description of ORG Projects in general",
                                      features=SUMMARY_RICHTEXT_FEATURES)
    introduction_image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name="Introduction Image",
        help_text="A high quality image related to Projects",
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

    items_per_page = models.PositiveIntegerField(default=6, validators=[
        MinValueValidator(6),
        MaxValueValidator(20),
    ], help_text="How many items should be visible on the projects landing page filter section ?")

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel('banner_image'),
                FieldPanel('banner_title'),
                FieldPanel('banner_subtitle'),
                FieldPanel('call_to_action_button_text'),
                PageChooserPanel('call_to_action_related_page', )
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
            ],
            heading="Introduction Section",
        ),
        MultiFieldPanel(
            [
                FieldPanel('items_per_page'),
            ],
            heading="Other Settings",
        ),
    ]

    @cached_property
    def filters(self):
        services = ServiceCategory.objects.all()
        return {'services': services}

    def filter_projects(self, request):
        projects = self.all_projects

        services = query_param_to_list(request.GET.get("service"), as_int=True)

        filters = models.Q()

        if services:
            filters &= models.Q(services__in=services)

        return projects.filter(filters).distinct()

    def filter_and_paginate_projects(self, request):
        page = request.GET.get('page')

        filtered_projects = self.filter_projects(request)

        paginated_projects = paginate(filtered_projects, page, self.items_per_page)

        return paginated_projects

    @cached_property
    def all_projects(self):
        return ProjectPage.objects.live().order_by('-end_date')

    def get_context(self, request, *args, **kwargs):
        context = super(ProjectIndexPage, self).get_context(
            request, *args, **kwargs)

        context['projects'] = self.filter_and_paginate_projects(request)

        return context

    def save(self, *args, **kwargs):
        # if not self.search_image and self.banner_image:
        #     self.search_image = self.banner_image
        if not self.search_description and self.introduction_text:
            p = get_first_non_empty_p_string(self.introduction_text)
            if p:
                # Limit the search meta desc to google's 160 recommended chars
                self.search_description = truncatechars(p, 160)
        return super().save(*args, **kwargs)


class ProjectPage(Page):
    template = 'project_page.html'
    parent_page_types = ['projects.ProjectIndexPage']
    subpage_types = []

    services = ParentalManyToManyField('core.ServiceCategory', through='ServiceProject', related_name='projects')

    banner_image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name="Project Banner Image",
        help_text="A high quality image related to this Project, that appears on the top banner",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    full_name = models.CharField(max_length=200, verbose_name="Project full name",
                                 help_text="Name of the project")
    short_name = models.CharField(max_length=50, verbose_name="Project short name",
                                  help_text="Short name of the project")

    call_to_action_button_text = models.CharField(max_length=20, blank=True, null=True)
    call_to_action_related_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    call_to_action_external_link = models.URLField(max_length=200, blank=True, null=True,
                                                   help_text="External Link if applicable")

    begin_date = models.DateField()
    end_date = models.DateField()

    introduction_title = models.TextField(help_text="This can be the main objective of the project in one sentence",
                                          verbose_name="Project Tagline")
    introduction_text = RichTextField(help_text="A description of this project", features=SUMMARY_RICHTEXT_FEATURES,
                                      verbose_name="Project summary")
    introduction_image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name="Introduction Image",
        help_text="A high quality image related this project",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    partners = ParentalManyToManyField('about.Partner', blank=True, related_name='projects') 

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
    goals_block = StreamField([
        ('goal', blocks.CollapsibleBlock()),
    ], null=True, blank=True, verbose_name="Goals", use_json_field=True)

    feature_block = StreamField([
        ('feature_item', blocks.FeatureBlock()),
    ], null=True, blank=True,  use_json_field=True)

    project_materials = StreamField([
        ('material', blocks.CategorizedAdditionalMaterialBlock())
    ], null=True, blank=True, use_json_field=True )
    youtube_playlist = models.ForeignKey(
        YoutubePlaylist,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    @cached_property
    def banner_title(self):
        return self.short_name

    @cached_property
    def banner_subtitle(self):
        return self.full_name

    @cached_property
    def period(self):
        return "{} {} - {} {}".format(calendar.month_name[self.begin_date.month], self.begin_date.year,
                                      calendar.month_name[self.end_date.month], self.end_date.year)

    @cached_property
    def progress(self):
        today = datetime.today()

        project_total_duration = relativedelta.relativedelta(self.end_date, self.begin_date)
        project_total_duration = project_total_duration.years * 12 + project_total_duration.months

        project_active_duration = relativedelta.relativedelta(today, self.begin_date)
        project_active_duration = project_active_duration.years * 12 + project_active_duration.months

        percentage_progress = (project_active_duration / project_total_duration) * 100

        if percentage_progress < 100:
            return percentage_progress
        else:
            return 100

    @cached_property
    def status(self):
        progress = self.progress
        if progress < 0:
            return "Planned"
        if progress < 100:
            return "In Progress"
        else:
            return "Complete"

    @cached_property
    def complete(self):
        return self.progress == 100

    @cached_property
    def publications(self):
        return PublicationPage.objects.live().filter(projects=self.pk).order_by('-publication_date')[:4]

    @cached_property
    def news(self):
        return NewsPage.objects.live().filter(projects=self.pk).order_by('-date')[:4]

    @cached_property
    def events(self):
        return EventPage.objects.live().filter(projects=self.pk, is_hidden=False).order_by('-date_from')[:4]

    content_panels = Page.content_panels + [
        FieldPanel('services', widget=CheckboxSelectMultiple),
        MultiFieldPanel(
            [
                FieldPanel('banner_image'),
                FieldPanel('full_name'),
                FieldPanel('short_name'),
                FieldPanel('begin_date'),
                FieldPanel('end_date'),
                FieldPanel('call_to_action_button_text'),
                PageChooserPanel('call_to_action_related_page', ),
                FieldPanel('call_to_action_external_link')

            ],
            heading="Banner Section / Project Details",
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
        FieldPanel('goals_block'),
        FieldPanel('feature_block'),
        FieldPanel('project_materials'),
        FieldPanel('youtube_playlist'),
        FieldPanel('partners', widget=CheckboxSelectMultiple),
    ]

    api_fields = [
        APIField('full_name'),
        APIField('short_name'),
        APIField('begin_date'),
        APIField('end_date'),
        APIField('complete'),
    ]

    class Meta:
        verbose_name = "Project"
        ordering = ['-end_date', ]

    def save(self, *args, **kwargs):
        # if not self.search_image and self.banner_image:
        #     self.search_image = self.banner_image
        if not self.search_description and self.introduction_title:
            # Limit the search meta desc to google's 160 recommended chars
            self.search_description = truncatechars(self.introduction_title, 160)
        return super().save(*args, **kwargs)


class ServiceProject(models.Model):
    service = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE)
    project = models.ForeignKey(ProjectPage, on_delete=models.CASCADE)
    position = PositionField(collection=('project', 'service'))

    class Meta(object):
        unique_together = ('service', 'project')
        ordering = ['position']

    def __str__(self):
        return '{} -  {}'.format(self.project.short_name, self.service.name)