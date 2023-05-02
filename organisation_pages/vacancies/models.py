from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.template.defaultfilters import truncatechars
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from rest_framework.fields import BooleanField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, PageChooserPanel
from wagtail.api import APIField
from wagtail.fields import RichTextField
from wagtail.models import Page
# from wagtailmetadata.models import MetadataPageMixin

from integrations.webicons.edit_handlers import WebIconChooserPanel
from core.utils import paginate, get_first_non_empty_p_string 
from nmhs_cms.settings.base import SUMMARY_RICHTEXT_FEATURES


class VacanciesPage(Page):
    template = 'vacancies_index_page.html'
    parent_page_types = ['about.AboutIndexPage']
    subpage_types = ['vacancies.VacancyDetailPage']
    max_count = 1
    show_in_menus = True

    banner_image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name=_("Banner Image"),
        help_text=_("A high quality image related to Vacancies"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    banner_title = models.CharField(max_length=255, verbose_name=_("Banner Title"))
    banner_subtitle = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Banner Subtitle"))

    call_to_action_button_text = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Call to action button text"))
    call_to_action_related_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Call to action related page")
    )

    introduction_title = models.CharField(max_length=100, help_text=_("Introduction section title"), verbose_name=_("Introduction Title"))
    introduction_text = RichTextField(help_text=_("A description of working at ORG"),
                                      features=SUMMARY_RICHTEXT_FEATURES, verbose_name=_("Introduction text"))
    introduction_image = models.ForeignKey(
        'webicons.WebIcon',
        help_text=_("A high quality illustration related to Working at ORG"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Vacancies SVG Illustration")
    )

    introduction_button_text = models.TextField(max_length=20, blank=True, null=True, verbose_name=_("Introduction button text"))
    introduction_button_link = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Introduction button link")
    )

    items_per_page = models.PositiveIntegerField(default=6, validators=[
        MinValueValidator(6),
        MaxValueValidator(20),
    ], help_text=_("How many items should be visible on the landing page filter section ?"),
    verbose_name=_("Items per page"))

    no_vacancies_header_text = models.TextField(blank=True, null=True,
                                                help_text=_("Text to appear when there are no vacancies"),
                                                verbose_name=_("No vacancies header text"))

    no_vacancies_description_text = models.TextField(blank=True, null=True,
                                                     help_text=_("Additional text to appear when there are no vacancies,"
                                                               "below the no vacancies header text"),
                                                               verbose_name=_("No vacancies description text"))

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel('banner_image'),
                FieldPanel('banner_title'),
                FieldPanel('banner_subtitle'),
                FieldPanel('call_to_action_button_text'),
                PageChooserPanel('call_to_action_related_page', )
            ],
            heading=_("Banner Section"),
        ),
        MultiFieldPanel(
            [
                FieldPanel('introduction_title'),
                WebIconChooserPanel('introduction_image'),
                FieldPanel('introduction_text'),
                FieldPanel('introduction_button_text'),
                PageChooserPanel('introduction_button_link'),
            ],
            heading=_("Introduction Section"),
        ),
        MultiFieldPanel(
            [
                FieldPanel('no_vacancies_header_text'),
                FieldPanel('no_vacancies_description_text'),
                FieldPanel('items_per_page'),
            ],
            heading=_("Other Settings"),
        ),
    ]

    def filter_vacancies(self, request):
        vacancies = self.all_vacancies

        is_open = request.GET.get("open")

        filters = models.Q()

        # By default get open tenders, i.e deadline still greater than today
        filters &= models.Q(deadline__gt=timezone.now())

        if is_open and is_open == "False":
            filters &= models.Q(deadline__lt=timezone.now())

        return vacancies.filter(filters)

    def filter_and_paginate_vacancies(self, request):
        page = request.GET.get('page')

        filtered_vacancies = self.filter_vacancies(request)

        paginated_projects = paginate(filtered_vacancies, page, self.items_per_page)

        return paginated_projects

    @cached_property
    def all_vacancies(self):
        return VacancyDetailPage.objects.live().order_by('-posting_date')

    def get_context(self, request, *args, **kwargs):
        context = super(VacanciesPage, self).get_context(
            request, *args, **kwargs)

        context['vacancies'] = self.filter_and_paginate_vacancies(request)

        return context

    def save(self, *args, **kwargs):
        #if not self.search_image and self.banner_image:
            #self.search_image = self.banner_image
        if not self.search_description and self.introduction_text:
            p = get_first_non_empty_p_string(self.introduction_text)
            if p:
                # Limit the search meta desc to google's 160 recommended chars
                self.search_description = truncatechars(p, 160)
        return super().save(*args, **kwargs)
    
    class Meta:
        verbose_name=_("Vacancy Page")


class VacancyDetailPage(Page):
    template = 'vacancy_detail_page.html'
    parent_page_types = ['vacancies.VacanciesPage']
    subpage_types = []

    posting_date = models.DateTimeField(default=timezone.now, verbose_name=_("Date of Posting"))
    duty_station = models.CharField(max_length=100, verbose_name=_("Duty Station"))
    deadline = models.DateTimeField(_("Application Deadline"))
    description = RichTextField(_("Job Description"), blank=True, null=True,
                                features=SUMMARY_RICHTEXT_FEATURES)
    duration = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Duration"))
    document = models.ForeignKey(
        'core.CustomDocumentModel',
        verbose_name=_("Downloadable Job Description Document"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text=_("Optional downloadable job description document")
    )

    content_panels = Page.content_panels + [
        FieldPanel('posting_date'),
        FieldPanel('duty_station'),
        FieldPanel('duration'),
        FieldPanel('description'),
        FieldPanel('deadline'),
        FieldPanel('document'),
    ]

    api_fields = [
        APIField('posting_date'),
        APIField('duty_station'),
        APIField('duration'),
        APIField('deadline'),
        APIField('document'),
        APIField('closed', serializer=BooleanField(source='is_closed')),
    ]

    class Meta:
        verbose_name=_("Vacancy Detail Page")

    @property
    def item_type(self):
        return "Vacancy"

    @cached_property
    def position_title(self):
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

    
    def save(self, *args, **kwargs):
        if not self.title.istitle():
            self.title = self.title.title()
        if not self.search_description and self.description:
            p = get_first_non_empty_p_string(self.description)
            if p:
                # Limit the search meta desc to google's 160 recommended chars
                self.search_description = truncatechars(p, 160)
        return super().save(*args, **kwargs)