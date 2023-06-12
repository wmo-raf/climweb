from django.db import models
from django.forms import CheckboxSelectMultiple
from django.utils.translation import gettext_lazy as _
from positions import PositionField
from wagtail.admin.panels import FieldPanel
from wagtail.admin.panels import PageChooserPanel
from wagtail.api import APIField
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.models import Site
from wagtail.snippets.models import register_snippet

from integrations.webicons.edit_handlers import WebIconChooserPanel
from integrations.webicons.models import WebIcon


@register_snippet
class ProductGroup(models.Model):
    name = models.CharField(max_length=255)
    icon = models.ForeignKey(WebIcon, on_delete=models.PROTECT)
    order = models.PositiveIntegerField(default=0)

    panels = [
        FieldPanel('name'),
        WebIconChooserPanel('icon'),
        FieldPanel('order')
    ]

    def __str__(self):
        return self.name

    @property
    def icon_url(self):
        return self.icon.url

    class Meta:
        verbose_name = "Product Group"
        verbose_name_plural = "Products Groups"
        ordering = ('order',)


@register_snippet
class ProductType(models.Model):
    RESOURCE_FORMAT_CHOICES = [
        ('png', 'PNG'),
        ('pdf', 'PDF'),
    ]

    PRODUCT_CLASSIFICATION_CHOICES = (
        ('forecast', 'Forecast'),
        ('monitoring', 'Monitoring'),
    )

    name = models.CharField(max_length=255)
    group = models.ForeignKey(ProductGroup, on_delete=models.PROTECT,
                              related_name='product_types')
    type = models.CharField(max_length=20, choices=RESOURCE_FORMAT_CHOICES)
    classification = models.CharField(max_length=100, choices=PRODUCT_CLASSIFICATION_CHOICES, default='forecast')
    ordering = models.PositiveIntegerField(default=0)

    panels = [
        FieldPanel('name'),
        FieldPanel('group'),
        FieldPanel('classification'),
        FieldPanel('ordering'),
    ]

    api_fields = [
        APIField('name'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Product Type"
        verbose_name_plural = "Products Types"
        ordering = ['ordering']


@register_snippet
class ProductCategory(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Name"))

    panels = [
        FieldPanel('name'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Product Category")
        verbose_name_plural = _("Products Categories")


@register_snippet
class ServiceCategory(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    # icon = models.CharField(max_length=100, null=True, blank=True, help_text="Humanitarian Icon")
    icon = models.ForeignKey(WebIcon, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("Icon"))

    panels = [
        FieldPanel('name'),
        # FieldPanel('icon', widget=IconChooserWidget),
        WebIconChooserPanel('icon'),
    ]

    api_fields = [
        APIField('name'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Service Category")
        verbose_name_plural = _("Service Categories")


@register_snippet
class PublicationType(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    icon = models.ForeignKey(WebIcon, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("Icon"))

    panels = [
        FieldPanel('name'),
        WebIconChooserPanel('icon'),
    ]

    api_fields = [
        APIField('name'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = _("Publication Types")


@register_snippet
class NewsType(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    is_alert = models.BooleanField(default=False, verbose_name=_("Is alert"))
    is_press_release = models.BooleanField(default=False, verbose_name=_("Is press release"))

    panels = [
        FieldPanel('name'),
        FieldPanel('is_alert'),
        FieldPanel('is_press_release'),
    ]

    api_fields = [
        APIField('name'),
        APIField('is_alert'),
        APIField('is_press_release'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("News Type")
        verbose_name_plural = _("News Types")


@register_snippet
class Application(models.Model):
    title = models.CharField(max_length=100, verbose_name=_("Title"))
    thumbnail = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Thumbnail")
    )
    url = models.URLField(verbose_name=_("URL"))
    services = models.ManyToManyField(ServiceCategory, through='ServiceApplication', related_name='applications',
                                      verbose_name=_("Services"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"))

    class Meta:
        ordering = ["order"]
        verbose_name = _("Application")

    panels = [
        FieldPanel('title'),
        FieldPanel('thumbnail'),
        FieldPanel('url'),
        FieldPanel('services', widget=CheckboxSelectMultiple),
        FieldPanel('order'),
    ]

    @property
    def thumbnail_url(self):
        site = Site.objects.filter(is_default_site=True).first()
        if self.thumbnail:
            return f"{site.root_url}{self.thumbnail.file.url}"
        return ""

    @property
    def thumbnail_url_lowres(self):
        site = Site.objects.filter(is_default_site=True).first()
        if self.thumbnail:
            rendition = self.thumbnail.get_rendition("original")
            lazy_image_path = lazy_image_url(rendition)
            return f"{site.root_url}{lazy_image_path}"

        return None

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("GIS Application")
        verbose_name_plural = _("GIS Applications")


class ServiceApplication(models.Model):
    service = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    position = PositionField(collection=('application', 'service'))

    class Meta(object):
        unique_together = ('service', 'application')
        ordering = ['position']

    def __str__(self):
        return '{} -  {}'.format(self.application.title, self.service.name)


@register_snippet
class EventType(models.Model):
    event_type = models.CharField(max_length=255, verbose_name=_("Event type"))
    icon = models.ForeignKey(WebIcon, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("Icon"))
    thumbnail = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text=_("Thumbnail/image for this type of event.")
    )

    def __str__(self):
        return self.event_type

    panels = [
        FieldPanel('event_type'),
        WebIconChooserPanel('icon'),
        FieldPanel('thumbnail'),
    ]

    api_fields = [
        APIField('event_type'),
        APIField('icon'),
    ]

    class Meta:
        verbose_name = _("Event Type")


@register_setting
class ImportantPages(BaseSiteSetting):
    mailing_list_signup_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("Mailing list sign up page"))
    contact_us_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("Contact us page"))
    all_products_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("All products page"))
    all_projects_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("All projects page"))
    all_alerts_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("All alerts page"))
    all_news_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("All news page"))
    all_publications_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("All publications page"))
    all_videos_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("All videos page"))
    all_applications_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("All applications page"))
    all_events_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("All events page"))
    all_partners_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("All partners page"))
    all_tenders_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("All tenders page"))
    all_vacancies_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("All vacancies page"))
    feedback_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("All feedback page"))

    panels = [
        PageChooserPanel('mailing_list_signup_page'),
        PageChooserPanel('contact_us_page'),
        PageChooserPanel('feedback_page'),
        PageChooserPanel('all_products_page'),
        PageChooserPanel('all_projects_page'),
        PageChooserPanel('all_tenders_page'),
        PageChooserPanel('all_vacancies_page'),
        PageChooserPanel('all_alerts_page'),
        PageChooserPanel('all_news_page'),
        PageChooserPanel('all_publications_page'),
        PageChooserPanel('all_videos_page'),
        PageChooserPanel('all_applications_page'),
        PageChooserPanel('all_events_page'),
        PageChooserPanel('all_partners_page'),
    ]
