from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, PageChooserPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page
from wagtail.snippets.models import register_snippet
from wagtailmetadata.models import MetadataPageMixin

from core import blocks
from core.models import AbstractBannerWithIntroPage
from nmhs_cms.settings.base import SUMMARY_RICHTEXT_FEATURES
from .blocks import TimelineBlock


class AboutIndexPage(MetadataPageMixin, Page):
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

    class Meta:
        verbose_name = _("About Index Page")


class AboutPage(AbstractBannerWithIntroPage):
    template = 'about_page.html'
    parent_page_types = ['about.AboutIndexPage']
    subpage_types = []
    max_count = 1
    show_in_menus_default = True

    mission = models.CharField(max_length=500, help_text=_("Organisation's mission"), null=True,
                               verbose_name=_("Organisation's mission"))
    vision = models.CharField(max_length=500, help_text=_("Organisation's vision"), null=True,
                              verbose_name=_("Organisation's vision"))

    timeline_heading = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Timeline Heading"))

    timeline = StreamField([
        ('nmhs_timeline', TimelineBlock()),
    ], null=True, blank=True, verbose_name=_("Timeline items"), use_json_field=True)

    org_struct_heading = models.CharField(max_length=250, help_text=_("Organisation's Structure Section Heading"),
                                          null=True, verbose_name=_("Organisation's Struture Heading"),
                                          default="Our Organisational Structure")
    org_struct_description = RichTextField(help_text=_("Organisation's Structure Description"), null=True,
                                           verbose_name=_("Organisation's Struture Description"),
                                           features=SUMMARY_RICHTEXT_FEATURES)
    org_struct_img = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name=_("Organisational Structure Image"),
        help_text=_("A high quality image related to your organisation's structure"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    feature_block = StreamField([
        ('feature_item', blocks.FeatureBlock()),
    ], null=True, blank=True, use_json_field=True, verbose_name=_("Feature Block"))

    additional_materials = StreamField([
        ('material', blocks.CategorizedAdditionalMaterialBlock())
    ], null=True, blank=True, use_json_field=True, verbose_name=_("Additional Materials"))

    bottom_call_to_action_heading = models.CharField(max_length=100, blank=True, null=True,
                                                     verbose_name=_("Bottom Call to action heading"))
    bottom_call_to_action_description = models.TextField(blank=True, null=True,
                                                         verbose_name=_("Bottom call to action description"))
    bottom_call_to_action_button_text = models.CharField(max_length=20, blank=True, null=True,
                                                         verbose_name=_("Bottom call to action button text"))
    bottom_call_to_action_button_link = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Bottom call to action button link")
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
            heading=_("Introduction Section"),
        ),
        MultiFieldPanel(
            [
                FieldPanel('mission'),
                FieldPanel('vision'),
            ],
            heading=_("Mission & Vision Section"),
        ),
        MultiFieldPanel(
            [
                FieldPanel('org_struct_heading'),
                FieldPanel('org_struct_description'),
                FieldPanel('org_struct_img'),
            ],
            heading=_("Organisation Structure Section"),
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
            heading=_("Bottom Call to action Section"),
        ),
    ]

    @property
    def partners(self):
        return Partner.objects.filter(is_main=True)[:5]

    class Meta:
        verbose_name = _("About Page")


@register_snippet
class Partner(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Name"))

    logo = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name=_("Logo")
    )

    link = models.URLField(max_length=500, blank=True, null=True,
                           help_text=_("Link to the partners website"),
                           verbose_name=_("Link to partner's website"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"))

    visible_on_homepage = models.BooleanField(default=False, verbose_name=_("Visible on Homepage"))
    is_main = models.BooleanField(default=False, verbose_name=_("Is Main"))

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('order',)
        verbose_name = _("Partner")

    panels = [
        FieldPanel('name'),
        FieldPanel('logo'),
        FieldPanel('link'),
        FieldPanel('order'),
        FieldPanel('visible_on_homepage'),
        FieldPanel('is_main'),
    ]


class PartnersPage(AbstractBannerWithIntroPage):
    template = 'partners.html'
    parent_page_types = ['about.AboutIndexPage']
    subpage_types = []
    max_count = 2
    show_in_menus_default = True

    partners_cta_title = models.CharField(max_length=100, verbose_name=_("Partners Call to Action title"),
                                          help_text=_("Partners call to action section title"))
    partners_cta_text = RichTextField(
        help_text=_("Call to action description text"),
        verbose_name=_("Partners call to action text"),
        features=SUMMARY_RICHTEXT_FEATURES)
    partners_cta_image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name=_("Partners call to action Image"),
        help_text=_("A high quality image related to the Partners call to action message"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    partners_cta_button_text = models.TextField(max_length=20, blank=True, null=True,
                                                verbose_name=_("Partners call to action button text"))
    partners_cta_button_link = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+', verbose_name=_("Partners call to action page")
    )
    content_panels = Page.content_panels + [
        *AbstractBannerWithIntroPage.content_panels,
        MultiFieldPanel(
            [
                FieldPanel('partners_cta_title'),
                FieldPanel('partners_cta_image'),
                FieldPanel('partners_cta_text'),
                FieldPanel('partners_cta_button_text'),
                PageChooserPanel('partners_cta_button_link'),
            ],
            heading=_("Partners Call to Action Section"),
        ),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super(PartnersPage, self).get_context(request, *args, **kwargs)
        context['partners'] = Partner.objects.all()
        return context

    class Meta:
        verbose_name = _("Partners Page")
