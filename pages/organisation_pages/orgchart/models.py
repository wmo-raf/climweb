
from wagtail.models import Page, Orderable
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField
from django.db import models
from wagtail.snippets.models import register_snippet
from django.utils.functional import cached_property
from base.models import AbstractBannerPage
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from base.mixins import MetadataPageMixin
from nmhs_cms.settings.base import SUMMARY_RICHTEXT_FEATURES
from wagtail.api import APIField
from django.db.models import Count


@register_snippet
class Department(models.Model):
    name = models.CharField(max_length=100)
    desc = RichTextField(features=SUMMARY_RICHTEXT_FEATURES, null=True, blank=True)
    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"))

    panels = [
        FieldPanel('name'),
        FieldPanel('desc'),
        FieldPanel('order')
    ]

    api_fields = [
        APIField('name'),
    ]

    def __str__(self):
        return f"{self.order}. {self.name}"
    
    class Meta:
        ordering = ['order']
    

class OrganisationChartPage(AbstractBannerPage):
    template = 'orgchart/orgchart_page.html'
    parent_page_types = ['organisation.OrganisationIndexPage']
    subpage_types = []
    show_in_menus_default = True

    max_count = 1

    introduction_heading = models.CharField(max_length=100, verbose_name=_('Introduction Heading'),
                                          help_text=_("Introduction section heading"), null=True, blank=True, default='MEET OUR TEAM')
    introduction_title = models.CharField(max_length=100, verbose_name=_('Introduction Title'),
                                          help_text=_("Introduction section title"), null=True, blank=True, default='Weather and Climate through Us')
    introduction_text = RichTextField(features=SUMMARY_RICHTEXT_FEATURES, verbose_name=_('Introduction text'),
                                      help_text=_("Introduction section description"), null=True, blank=True, default="We're a team of scientists, meteroologist, analysists, software engineers and researchers.We are invigorated by challenging weather phenomena, thrive on surpassing previous records, and are dedicated to improving the world's conditions with each passing day. ")
    
    content_panels = Page.content_panels + [
        *AbstractBannerPage.content_panels,
        MultiFieldPanel([
            FieldPanel('introduction_title'),
            FieldPanel('introduction_text'),
        ], heading=_('Introduction Section')),
        InlinePanel('employees', heading=_("Employee"), label=_("Employee")),
    ]

    @cached_property
    def all_departments(self):
        # Annotate the queryset with the count of employees per department
        departments_with_employee_count = Employee.objects.values('department__name').annotate(employee_count=Count('department')).order_by('department__order')

        # Filter departments with at least one employee
        departments_with_employees = departments_with_employee_count.filter(employee_count__gt=0)

        return departments_with_employees
    
    class Meta:
        verbose_name = _("Staff/Management Page")
    

class Employee(Orderable):
    page = ParentalKey(OrganisationChartPage, on_delete=models.CASCADE, related_name="employees")
    name = models.CharField(max_length=100,verbose_name=_("Staff's name"),
                                            help_text=_("First and Last names of staff"))
    role = models.CharField(max_length=100, verbose_name=_("Staff's role"),
                                            help_text=_("The role/position of the staff"))
    bio = RichTextField(features=SUMMARY_RICHTEXT_FEATURES, null=True, blank=True,verbose_name=_("Staff Biography"),
                                            help_text=_("Optional Summary biography of the staff"))
    department = models.ForeignKey(Department, on_delete=models.PROTECT, blank=False, null=True,
                                                  verbose_name=_("Staff's Department"))
    photo = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name=_("Staff Profile Image"),
        help_text=_("A high quality square image"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("role"),
        FieldPanel("bio"),
        FieldPanel("department"),
        FieldPanel("photo")
    ]

    class Meta:
        verbose_name = "{name} ({role})"
        verbose_name_plural = "{name} ({role})"
        ordering = ['sort_order']


    def __str__(self):
        return self.name
    
