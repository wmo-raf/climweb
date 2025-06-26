from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.template.defaultfilters import truncatechars
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from rest_framework.fields import BooleanField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.api import APIField
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page

from climweb.base import blocks
from climweb.base.mixins import MetadataPageMixin
from climweb.base.models import AbstractBannerWithIntroPage
from climweb.base.utils import paginate, get_first_non_empty_p_string
from climweb.config.settings.base import SUMMARY_RICHTEXT_FEATURES


class TendersPage(AbstractBannerWithIntroPage):
    template = 'tenders_index_page.html'
    parent_page_types = ['organisation.OrganisationIndexPage']
    subpage_types = ['tenders.TenderDetailPage']
    max_count = 1
    show_in_menus_default = True
    
    no_tenders_header_text = models.TextField(blank=True, null=True,
                                              help_text=_("Text to appear when there are no tenders"),
                                              verbose_name=_("No tenders header text"))
    
    no_tenders_description_text = models.TextField(blank=True, null=True,
                                                   help_text=_("Additional text to appear when there are no tenders,"
                                                               "below the no tenders header text"),
                                                   verbose_name=_("No tenders description text"))
    
    items_per_page = models.PositiveIntegerField(default=6, validators=[
        MinValueValidator(6),
        MaxValueValidator(20),
    ], help_text=_("How many items should be visible on the landing page filter section ?"),
                                                 verbose_name=_("Items per page"))
    
    content_panels = Page.content_panels + [
        *AbstractBannerWithIntroPage.content_panels,
        MultiFieldPanel(
            [
                FieldPanel('no_tenders_header_text'),
                FieldPanel('no_tenders_description_text'),
                FieldPanel('items_per_page'),
            ],
            heading=_("Other Settings"),
        ),
    ]
    
    def get_meta_image(self):
        meta_image = super().get_meta_image()
        
        if not meta_image:
            meta_image = self.get_parent().specific.get_meta_image()
        
        return meta_image
    
    def filter_tenders(self, request):
        tenders = self.all_tenders
        
        is_open = request.GET.get("open")
        
        filters = models.Q()
        
        # By default get open tenders, i.e deadline still greater than today
        filters &= models.Q(deadline__gte=timezone.now())
        
        if is_open and is_open == "False":
            filters &= models.Q(deadline__lt=timezone.now())
        
        return tenders.filter(filters)
    
    def filter_and_paginate_tenders(self, request):
        page = request.GET.get('page')
        
        filtered_tenders = self.filter_tenders(request)
        
        paginated_tenders = paginate(filtered_tenders, page, self.items_per_page)
        
        return paginated_tenders
    
    @cached_property
    def all_tenders(self):
        return TenderDetailPage.objects.live().order_by('-posting_date')
    
    def get_context(self, request, *args, **kwargs):
        context = super(TendersPage, self).get_context(
            request, *args, **kwargs)
        
        context['tenders'] = self.filter_and_paginate_tenders(request)
        
        return context
    
    class Meta:
        verbose_name = _("Tender Page")
    
    @cached_property
    def listing_image(self):
        if self.banner_image:
            return self.banner_image
        if self.introduction_image:
            return self.introduction_image
        return None


class TenderDetailPage(MetadataPageMixin, Page):
    template = 'tender_detail_page.html'
    parent_page_types = ['tenders.TendersPage']
    subpage_types = []
    
    posting_date = models.DateTimeField(default=timezone.now, verbose_name=_("Date of Posting"))
    ref_no = models.CharField(_("Reference Number"), max_length=100, blank=True, null=True,
                              help_text=_("Any Reference number if available"))
    deadline = models.DateTimeField(_("Submission Deadline"))
    description = RichTextField(blank=True, null=True, features=SUMMARY_RICHTEXT_FEATURES,
                                verbose_name=_("Description"))
    tender_document = models.ForeignKey(
        'base.CustomDocumentModel',
        verbose_name=_("Downloadable tender description document"),
        on_delete=models.PROTECT,
        related_name='+',
    )
    additional_documents = StreamField([
        ('additional_documents', blocks.AdditionalMaterialBlock()),
    ], null=True, blank=True, use_json_field=True, verbose_name=_("Additional Documents"))
    
    content_panels = Page.content_panels + [
        FieldPanel('posting_date'),
        FieldPanel('ref_no'),
        FieldPanel('deadline'),
        FieldPanel("description"),
        FieldPanel('tender_document'),
        FieldPanel('additional_documents', heading=_("Additional Documents")),
    ]
    
    api_fields = [
        APIField('posting_date'),
        APIField('deadline'),
        APIField('tender_document'),
        APIField('closed', serializer=BooleanField(source='is_closed')),
    ]
    
    class Meta:
        verbose_name = _("Tender Detail Page")
    
    @property
    def item_type(self):
        return "Tender"
    
    @cached_property
    def tender_title(self):
        return self.title
    
    @cached_property
    def is_new(self):
        difference = (timezone.now() - self.posting_date).days
        if difference < 10:
            return True
        return False
    
    @cached_property
    def days_to_deadline(self):
        today = timezone.now()
        time_delta = (self.deadline - today).days
        
        return time_delta
    
    @property
    def is_closed(self):
        difference = (timezone.now() - self.deadline).days
        if difference >= 0:
            return True
        return False
    
    @property
    def listing_summary(self):
        p = get_first_non_empty_p_string(self.description)
        if p:
            # Limit the search meta desc to google's 160 recommended chars
            return truncatechars(p, 160)
        
        return None
    
    def get_meta_image(self):
        meta_image = super().get_meta_image()
        
        if not meta_image:
            meta_image = self.get_parent().specific.get_meta_image()
        
        return meta_image
    
    def get_meta_description(self):
        meta_description = super().get_meta_description()
        
        if not meta_description:
            meta_description = self.listing_summary
        
        return meta_description
