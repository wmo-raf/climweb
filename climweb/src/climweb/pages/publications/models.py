from datetime import date, datetime

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.forms.widgets import CheckboxSelectMultiple
from django.template.defaultfilters import truncatechars
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalManyToManyField, ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import (FieldPanel, MultiFieldPanel)
from wagtail.api import APIField
from wagtail.fields import RichTextField
from wagtail.models import Page
from wagtail.snippets.models import register_snippet
from wagtailiconchooser.widgets import IconChooserWidget

from climweb.base.mixins import MetadataPageMixin
from climweb.base.models import ServiceCategory, AbstractBannerPage
from climweb.base.utils import paginate, query_param_to_list, get_first_non_empty_p_string
from climweb.config.settings.base import SUMMARY_RICHTEXT_FEATURES


class PageView(models.Model):
    """Model to track page views for analytics"""
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=_("IP Address"))
    user_agent = models.TextField(blank=True, null=True, verbose_name=_("User Agent"))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("View Timestamp"))
    session_key = models.CharField(max_length=40, blank=True, null=True, verbose_name=_("Session Key"))
    
    class Meta:
        verbose_name = _("Page View")
        verbose_name_plural = _("Page Views")
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"View of {self.content_object} at {self.timestamp}"

    @classmethod
    def record_view(cls, content_object, request=None, ip_address=None, user_agent=None, session_key=None):
        """
        Record a page view for the given content object.
        
        Args:
            content_object: The object being viewed (e.g., PublicationPage)
            request: HttpRequest object (optional, used to extract IP, user agent, session)
            ip_address: Manual IP address override
            user_agent: Manual user agent override  
            session_key: Manual session key override
        """
        # Additional checks if request is provided
        if request:
            # Don't track views for authenticated users
            if request.user.is_authenticated:
                return None
            
            # Don't track views in preview mode
            if getattr(request, 'is_preview', False):
                return None
            
            # Don't track views from bots/crawlers (basic check)
            user_agent_check = request.META.get('HTTP_USER_AGENT', '').lower()
            bot_indicators = ['bot', 'crawler', 'spider', 'scraper', 'wget', 'curl']
            if any(indicator in user_agent_check for indicator in bot_indicators):
                return None
        
        # Extract information from request if provided
        if request:
            if not ip_address:
                # Try to get real IP from headers (for proxy setups)
                ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
                if ip_address:
                    # Take the first IP in case of multiple proxies
                    ip_address = ip_address.split(',')[0].strip()
                else:
                    ip_address = request.META.get('REMOTE_ADDR')
            
            if not user_agent:
                user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            if not session_key and hasattr(request, 'session'):
                session_key = request.session.session_key
        
        # Create the view record
        return cls.objects.create(
            content_object=content_object,
            ip_address=ip_address,
            user_agent=user_agent,
            session_key=session_key
        )

    @classmethod
    def should_track_view(cls, request):
        """
        Check if a view should be tracked based on request conditions.
        
        Args:
            request: HttpRequest object
            
        Returns:
            bool: True if the view should be tracked, False otherwise
        """
        # Don't track if not a GET request
        if request.method != 'GET':
            return False
            
        # Don't track authenticated users
        if request.user.is_authenticated:
            return False
            
        # Don't track preview mode
        if getattr(request, 'is_preview', False):
            return False
            
        # Don't track bots/crawlers
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        bot_indicators = ['bot', 'crawler', 'spider', 'scraper', 'wget', 'curl']
        if any(indicator in user_agent for indicator in bot_indicators):
            return False
            
        # Check if internal tracking is enabled in settings
        try:
            from climweb.base.models import IntegrationSettings
            integration_settings = IntegrationSettings.for_request(request)
            return integration_settings and integration_settings.track_internally
        except Exception:
            return False


@register_snippet
class PublicationType(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    icon = models.CharField(max_length=100, null=True, blank=True)
    
    panels = [
        FieldPanel('name'),
        FieldPanel('icon', widget=IconChooserWidget),
    ]
    
    api_fields = [
        APIField('name'),
    ]
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = _("Publication Types")


class PublicationsIndexPage(AbstractBannerPage):
    template = 'publications_index_page.html'
    parent_page_types = ['home.HomePage', ]
    subpage_types = ['publications.PublicationPage']
    max_count = 1
    show_in_menus_default = True
    
    earliest_publication_year = models.PositiveIntegerField(
        default=datetime.now().year,
        validators=[
            MinValueValidator(2000),
            MaxValueValidator(datetime.now().year),
        ],
        help_text=_("The year for the earliest available publication. This is used to generate the years available for "
                    "filtering "), verbose_name=_("Earliest Publication Year"))
    publications_per_page = models.PositiveIntegerField(default=6, validators=[
        MinValueValidator(6),
        MaxValueValidator(20),
    ], help_text=_("How many publications per page should be visible on the all publications section ?"))
    
    content_panels = Page.content_panels + [
        *AbstractBannerPage.content_panels,
        MultiFieldPanel(
            [
                FieldPanel('publications_per_page'),
                FieldPanel('earliest_publication_year'),
            ],
            heading="Other Settings",
        ),
    ]
    
    class Meta:
        verbose_name = _("Publications Index Page")
    
    @cached_property
    def filters(self):
        from climweb.pages.organisation_pages.projects.models import ProjectPage
        publication_types = PublicationType.objects.all()
        service_categories = ServiceCategory.objects.all()
        projects = ProjectPage.objects.live()
        years = PublicationPage.objects.dates("publication_date", 'year')
        
        return {
            'publication_types': publication_types,
            'service_categories': service_categories,
            'year': years,
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


class PublicationPageTag(TaggedItemBase):
    content_object = ParentalKey('publications.PublicationPage', on_delete=models.CASCADE,
                                 related_name='publications_tags', )


class PublicationPage(MetadataPageMixin, Page):
    template = 'publication_page.html'
    parent_page_types = ['publications.PublicationsIndexPage']
    subpage_types = []
    
    publication_type = models.ForeignKey(PublicationType, on_delete=models.PROTECT, verbose_name=_("Publication Type"))
    categories = ParentalManyToManyField('base.ServiceCategory', verbose_name=_("Services related to this publication"))
    projects = ParentalManyToManyField('projects.ProjectPage', blank=True, verbose_name=_("Relevant Projects"))
    summary = RichTextField(features=SUMMARY_RICHTEXT_FEATURES, verbose_name=_("Summary"))
    publication_date = models.DateField(_("Date of Publish"), default=date.today)
    is_visible_on_homepage = models.BooleanField(default=False,
                                                 help_text="Should this appear in the homepage as"
                                                           " an alert/latest update ?",
                                                 verbose_name=_("Is visible on homepage"))
    featured = models.BooleanField(
        _("Mark as featured"), default=False,
        help_text=_("Featured publications appear on the publications landing page"))
    period_start_date = models.DateField(blank=True, null=True,
                                         help_text=_("Optional start date for which this publication is relevant"),
                                         verbose_name=_("Start date"))
    period_end_date = models.DateField(blank=True, null=True,
                                       help_text="Optional end date for which this publication is relevant",
                                       verbose_name=_("End date"))
    peer_reviewed = models.BooleanField(default=False, help_text="Is this a peer reviewed publication ?",
                                        verbose_name=_("Peer reviewed"))
    
    thumbnail = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Publication Image (Thumbnail)"),
        help_text=_("This can be a screenshot of the front page of the publication. "
                    "If left empty and Auto-generate above is checked and the uploaded document is a PDF, an image of the "
                    "first page will be auto-generated.")
    )
    auto_generate_thumbnail = models.BooleanField(
        default=True,
        help_text=_("If the document is a PDF, an image of the first page will be auto-generated."),
        verbose_name=_("Auto-generate thumbnail")
    )
    
    document = models.ForeignKey(
        'base.CustomDocumentModel',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='+',
        verbose_name=_("Document or File"),
        help_text=_("Here you can upload pdfs, word documents, powerpoints, zip files or any other file")
    )
    external_publication_url = models.URLField(max_length=500, blank=True, null=True,
                                               verbose_name=_(
                                                   "External Url - *Only If published/hosted somewhere else"),
                                               help_text=_("Link to published resource if external"))
    
    tags = ClusterTaggableManager(through=PublicationPageTag, blank=True, verbose_name=_("Tags"))
    
    content_panels = Page.content_panels + [
        FieldPanel('publication_type'),
        FieldPanel('categories', widget=CheckboxSelectMultiple),
        FieldPanel('projects', widget=CheckboxSelectMultiple),
        FieldPanel('publication_date'),
        FieldPanel('document'),
        FieldPanel('auto_generate_thumbnail'),
        FieldPanel('thumbnail'),
        FieldPanel('external_publication_url'),
        FieldPanel('summary'),
        FieldPanel('featured'),
        FieldPanel('is_visible_on_homepage'),
        FieldPanel('peer_reviewed'),
        MultiFieldPanel([
            FieldPanel('period_start_date'),
            FieldPanel('period_end_date'),
        ], heading=_("Additional Details")),
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
    
    class Meta:
        verbose_name = "Publication"
    
    def save(self, *args, **kwargs):
        if self.document and self.auto_generate_thumbnail:
            self.thumbnail = self.document.get_thumbnail()
        
        super(PublicationPage, self).save(*args, **kwargs)
    
    @cached_property
    def publication_title(self):
        return self.title
    
    @property
    def listing_summary(self):
        p = get_first_non_empty_p_string(self.summary)
        if p:
            # Limit the search meta desc to google's 160 recommended chars
            return truncatechars(p, 160)
        return None
    
    @property
    def view_count(self):
        """Get the total number of views for this publication"""
        try:
            from django.contrib.contenttypes.models import ContentType
            content_type = ContentType.objects.get_for_model(self)
            return PageView.objects.filter(content_type=content_type, object_id=self.pk).count()
        except Exception:
            return 0
    
    def record_view(self, request=None, **kwargs):
        """Record a view of this publication page"""
        try:
            view_record = PageView.record_view(self, request=request, **kwargs)
            print(f"Recorded view for {self.title}: {view_record}")
            return view_record
        except Exception as e:
            print(f"Error in record_view: {e}")
            return None

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
            "card_text": self.listing_summary,
            "card_full_text": self.summary,
            "card_meta": self.publication_date,
            "card_more_link": self.url,
            "card_tag": "Publication",
            "card_file": card_file,
            "card_external_publication_url": self.external_publication_url,
            "card_tags": card_tags,
            "card_views": self.view_count,
            "card_ga_label": "Publication",
        }
        
        return props
    
    def serve(self, request, *args, **kwargs):
        """Override serve to record page views when the publication is accessed"""
        try:
            # Only record views for GET requests from non-authenticated users and not in preview mode
            if (request.method == 'GET' and 
                not request.user.is_authenticated and 
                not getattr(request, 'is_preview', False)):
                
                # Check if internal tracking is enabled in settings
                from climweb.base.models import IntegrationSettings
                try:
                    integration_settings = IntegrationSettings.for_request(request)
                    if integration_settings and integration_settings.track_internally:
                        self.record_view(request)
                except Exception:
                    # If settings are not available, don't track views
                    pass
        except Exception as e:
            # Log the error for debugging but continue serving the page
            print(f"Error recording page view: {e}")
        
        return super().serve(request, *args, **kwargs)

    def get_context(self, request, *args, **kwargs):
        context = super(PublicationPage, self).get_context(request, *args, **kwargs)
        
        context['related_items'] = self.related_items
        
        return context
    
    def get_meta_image(self):
        meta_image = super().get_meta_image()
        
        if not meta_image and self.thumbnail:
            meta_image = self.thumbnail
        
        if not meta_image:
            parent = self.get_parent()
            if hasattr(parent, 'get_meta_image'):
                meta_image = parent.get_meta_image()
        
        return meta_image
    
    def get_meta_description(self):
        meta_description = super().get_meta_description()
        
        if not meta_description:
            meta_description = self.listing_summary
        
        return meta_description
