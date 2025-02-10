from datetime import datetime

from dateutil import relativedelta
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.forms import CheckboxSelectMultiple
from django.template.defaultfilters import truncatechars
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalManyToManyField
from positions import PositionField
from wagtail.admin.panels import (FieldPanel, MultiFieldPanel)
from wagtail.fields import StreamField
from wagtail.models import Page

from climweb.base import blocks
from climweb.base.models import ServiceCategory, AbstractBannerWithIntroPage
from climweb.base.utils import query_param_to_list, paginate, get_first_non_empty_p_string
from climweb.pages.events.models import EventPage
from climweb.pages.news.models import NewsPage
from climweb.pages.publications.models import PublicationPage
from climweb.pages.videos.models import YoutubePlaylist


class ProjectIndexPage(AbstractBannerWithIntroPage):
    template = 'project_index_page.html'
    parent_page_types = ['organisation.OrganisationIndexPage']
    subpage_types = ['projects.ProjectPage']
    max_count = 1
    show_in_menus_default = True
    
    items_per_page = models.PositiveIntegerField(default=6, validators=[
        MinValueValidator(6),
        MaxValueValidator(20),
    ], help_text=_("How many items should be visible on the projects landing page filter section ?"),
                                                 verbose_name=_("Items per page"))
    
    content_panels = Page.content_panels + [
        *AbstractBannerWithIntroPage.content_panels,
        MultiFieldPanel(
            [
                FieldPanel('items_per_page'),
            ],
            heading=_("Other Settings"),
        ),
    ]
    
    @cached_property
    def listing_image(self):
        if self.banner_image:
            return self.banner_image
        if self.introduction_image:
            return self.introduction_image
        return None
    
    @cached_property
    def filters(self):
        services = ServiceCategory.objects.all()
        years = ProjectPage.objects.dates("begin_date", "year")
        return {'services': services, "year": years}
    
    def filter_projects(self, request):
        projects = self.all_projects
        
        services = query_param_to_list(request.GET.get("service"), as_int=True)
        years = query_param_to_list(request.GET.get("year"))
        
        filters = models.Q()
        
        if services:
            filters &= models.Q(services__in=services)
        
        if years:
            filters &= models.Q(begin_date__year__in=years)
        
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
    
    class Meta:
        verbose_name = _("Project Index Page")


class ProjectPage(AbstractBannerWithIntroPage):
    template = 'project_page.html'
    parent_page_types = ['projects.ProjectIndexPage']
    subpage_types = []
    
    services = ParentalManyToManyField('base.ServiceCategory', through='ServiceProject', related_name='projects',
                                       verbose_name=_("Services"))
    full_name = models.CharField(max_length=200, verbose_name=_("Project full name"),
                                 help_text=_("Name of the project"))
    short_name = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Project short name"),
                                  help_text=_("Short name of the project"))
    
    begin_date = models.DateField(verbose_name=_("Begin date"))
    end_date = models.DateField(verbose_name=_("End date"), blank=True, null=True)
    
    partners = ParentalManyToManyField('partners.Partner', blank=True, related_name='projects',
                                       verbose_name=_("Partners"))
    
    goals_title = models.CharField(max_length=200, blank=True, null=True, default="Our Areas of Work",
                                   verbose_name=_("Goals/Activities section title"))
    goals_block = StreamField([
        ('goal', blocks.CollapsibleBlock(label=_("Goal/Activity")))
    ], null=True, blank=True, verbose_name=_("Goals/Activities List"), use_json_field=True)
    
    feature_block = StreamField([
        ('feature_item', blocks.FeatureBlock()),
    ], null=True, blank=True, use_json_field=True, verbose_name=_("Feature block"))
    
    project_materials = StreamField([
        ('material', blocks.CategorizedAdditionalMaterialBlock())
    ], null=True, blank=True, use_json_field=True, verbose_name=_("Project Materials"))
    youtube_playlist = models.ForeignKey(
        YoutubePlaylist,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Youtube playlist")
    )
    
    content_panels = Page.content_panels + [
        FieldPanel('services', widget=CheckboxSelectMultiple),
        *AbstractBannerWithIntroPage.content_panels,
        FieldPanel('full_name'),
        FieldPanel('short_name'),
        FieldPanel('begin_date'),
        FieldPanel('end_date'),
        MultiFieldPanel(
            [
                FieldPanel('goals_title'),
                FieldPanel('goals_block'),
            ],
            heading=_("Project Goals/Activities Section")
        ),
        FieldPanel('feature_block'),
        FieldPanel('project_materials'),
        FieldPanel('youtube_playlist'),
        FieldPanel('partners', widget=CheckboxSelectMultiple),
    ]
    
    @cached_property
    def period(self):
        if not self.end_date:
            return self.begin_date.strftime("%B %Y")
        
        return f"{self.begin_date.strftime('%B %Y')} - {self.end_date.strftime('%B %Y')}"
    
    @cached_property
    def label(self):
        if self.short_name:
            return self.short_name
        else:
            return self.full_name
    
    @cached_property
    def progress(self):
        if not self.end_date:
            return None
        
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
        if not self.progress:
            return None
        
        if self.progress < 0:
            return _("Planned")
        if self.progress < 100:
            return _("Ongoing")
        else:
            return _("Complete")
    
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
    
    class Meta:
        verbose_name = _("Project")
        ordering = ['-end_date', ]
    
    def save(self, *args, **kwargs):
        # if not self.search_image and self.banner_image:
        # self.search_image = self.banner_image
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
