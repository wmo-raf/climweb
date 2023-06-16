from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, PageChooserPanel
from wagtail.fields import RichTextField
from wagtail.models import Page
from wagtail.snippets.models import register_snippet

from base.models import AbstractBannerWithIntroPage
from nmhs_cms.settings.base import SUMMARY_RICHTEXT_FEATURES


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
    template = 'partners/partners.html'
    parent_page_types = ['organisation.OrganisationIndexPage']
    subpage_types = []
    max_count = 1
    show_in_menus_default = True

    partners_cta_title = models.CharField(max_length=100, blank=True, null=True,
                                          verbose_name=_("Partners Call to Action title"),
                                          help_text=_("Partners call to action section title"))
    partners_cta_text = RichTextField(
        blank=True, null=True,
        features=SUMMARY_RICHTEXT_FEATURES,
        verbose_name=_("Partners call to action text"),
        help_text=_("Call to action description text"),
    )
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

    @cached_property
    def listing_image(self):
        if self.banner_image:
            return self.banner_image
        if self.introduction_image:
            return self.introduction_image
        return None

    def get_context(self, request, *args, **kwargs):
        context = super(PartnersPage, self).get_context(request, *args, **kwargs)
        context['partners'] = Partner.objects.all()
        return context

    class Meta:
        verbose_name = _("Partners Page")
