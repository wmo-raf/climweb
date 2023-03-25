from django.db import models
from positions import PositionField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, PageChooserPanel
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page
from wagtail.snippets.models import register_snippet

from cms_pages.webicons.edit_handlers import WebIconChooserPanel
from core import blocks
from nmhs_cms.settings.base import SUMMARY_RICHTEXT_FEATURES
from .blocks import TimelineBlock 

class AboutIndexPage(Page):
    parent_page_types = ['home.HomePage']
    # template = ''
    max_count = 1
    subpage_types = [
        'about.AboutPage',
        'about.PartnersPage',
        'vacancies.VacanciesPage',
        'projects.ProjectIndexPage',
        'tenders.TendersPage'
    ]
    show_in_menus_default = True

class AboutPage(Page):
    template = 'about_page.html'
    parent_page_types = ['about.AboutIndexPage']
    subpage_types = []
    max_count = 1
    show_in_menus_default = True

    introduction_title = models.CharField(max_length=100, help_text="Introduction section title")
    introduction_text = RichTextField(help_text="A short summary of your organisation as an organisation")
    introduction_image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name="Introduction Image",
        help_text="A high quality image related to your organisation as an organisation",
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

    mission = models.CharField(max_length=500, help_text="Organisation's mission", null=True, verbose_name = "Organisation's mission")
    vision = models.CharField(max_length=500, help_text="Organisation's vision", null=True, verbose_name= "Organisation's vision")

    timeline_heading = models.CharField(max_length=255, blank=True, null=True)

    timeline = StreamField([
        ('nmhs_timeline', TimelineBlock()),
    ], null=True, blank=True, verbose_name="Timeline items", use_json_field=True)


    org_struct_heading = models.CharField(max_length=250, help_text="Organisation's Structure Section Heading", null=True, verbose_name = "Organisation's Struture Heading", default="Our Organisational Structure")
    org_struct_description = RichTextField( help_text="Organisation's Structure Description", null=True, verbose_name = "Organisation's Struture Description", features=SUMMARY_RICHTEXT_FEATURES)
    org_struct_img = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name="Organisational Structure Image",
        help_text="A high quality image related to your organisation's structure",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    feature_block = StreamField([
        ('feature_item', blocks.FeatureBlock()),
    ], null=True, blank=True, use_json_field=True)

    additional_materials = StreamField([
        ('material', blocks.CategorizedAdditionalMaterialBlock())
    ], null=True, blank=True,use_json_field=True )

    bottom_call_to_action_heading = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bottom Call to action heading")
    bottom_call_to_action_description = models.TextField(blank=True, null=True)
    bottom_call_to_action_button_text = models.CharField(max_length=20, blank=True, null=True)
    bottom_call_to_action_button_link = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    content_panels = Page.content_panels + [
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
                FieldPanel('mission'),
                FieldPanel('vision'),
            ],
            heading="Mission & Vision Section",
        ),
        MultiFieldPanel(
            [
                FieldPanel('org_struct_heading'),
                FieldPanel('org_struct_description'),
                FieldPanel('org_struct_img'),
            ],
            heading="Organisation Structure Section",
        ),
        MultiFieldPanel([
            FieldPanel('timeline_heading'),
            FieldPanel('timeline'),
        ], heading="Historical Timeline Section"),
        FieldPanel('additional_materials'),
        FieldPanel('feature_block'),
        MultiFieldPanel(
            [
                FieldPanel('bottom_call_to_action_heading'),
                FieldPanel('bottom_call_to_action_description'),
                FieldPanel('bottom_call_to_action_button_text'),
                PageChooserPanel('bottom_call_to_action_button_link'),
            ],
            heading="Bottom Call to action Section",
        ),
    ]

    @property
    def partners(self):
        return Partner.objects.filter(is_main=True)[:5]


@register_snippet
class Partner(models.Model):
    name = models.CharField(max_length=100)

    logo = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+'
    )

    link = models.URLField(max_length=500, blank=True, null=True,
                           help_text="Link to the partners website",
                           verbose_name="Link to partner's website")
    order = models.PositiveIntegerField(default=0)

    visible_on_homepage = models.BooleanField(default=False)
    is_main = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('order',)

    panels = [
        FieldPanel('name'),
        FieldPanel('logo'),
        FieldPanel('link'),
        FieldPanel('order'),
        FieldPanel('visible_on_homepage'),
        FieldPanel('is_main'),
    ]


class PartnersPage(Page):
    template = 'partners.html'
    parent_page_types = ['about.AboutIndexPage']
    subpage_types = []
    max_count = 2
    show_in_menus_default = True

    banner_image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name="Banner Image",
        help_text="A high quality image related to Partners",
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
    introduction_text = RichTextField(
        help_text="A summary of your organisation relations with partners",
        features=SUMMARY_RICHTEXT_FEATURES)

    introduction_image = models.ForeignKey(
        'webicons.WebIcon',
        verbose_name="Partners SVG Illustration",
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

    partners_cta_title = models.CharField(max_length=100, verbose_name="Partners Call to Action title",
                                          help_text="Partners call to action section title")
    partners_cta_text = RichTextField(
        help_text="Call to action description text",
        verbose_name="Partners call to action text",
        features=SUMMARY_RICHTEXT_FEATURES)
    partners_cta_image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name="Partners call to action Image",
        help_text="A high quality image related to the Partners call to action message",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    partners_cta_button_text = models.TextField(max_length=20, blank=True, null=True,
                                                verbose_name="Partners call to action button text")
    partners_cta_button_link = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+', verbose_name="Partners call to action page"
    )
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
                WebIconChooserPanel('introduction_image'),
                FieldPanel('introduction_text'),
                FieldPanel('introduction_button_text'),
                PageChooserPanel('introduction_button_link'),
            ],
            heading="Introduction Section",
        ),
        MultiFieldPanel(
            [
                FieldPanel('partners_cta_title'),
                FieldPanel('partners_cta_image'),
                FieldPanel('partners_cta_text'),
                FieldPanel('partners_cta_button_text'),
                PageChooserPanel('partners_cta_button_link'),
            ],
            heading="Partners Call to Action Section",
        ),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super(PartnersPage, self).get_context(request, *args, **kwargs)
        context['partners'] = Partner.objects.all()
        return context