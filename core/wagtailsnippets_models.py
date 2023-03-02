from django.db import models
from django.forms import CheckboxSelectMultiple

from wagtail.admin.panels import FieldPanel
from wagtail.api import APIField
from wagtail.models import Site

from cms_pages.webicons.models import WebIcon
from cms_pages.webicons.edit_handlers import WebIconChooserPanel
from positions import PositionField
from wagtail.snippets.models import register_snippet
from wagtail_lazyimages.templatetags.lazyimages_tags import lazy_image
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.admin.panels import PageChooserPanel
@register_snippet
class ServiceCategory(models.Model):
    name = models.CharField(max_length=255)

    panels = [
        FieldPanel('name'),
    ]

    api_fields = [
        APIField('name'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Service Category"
        verbose_name_plural = "Service Categories"


@register_snippet
class ProductCategory(models.Model):
    name = models.CharField(max_length=255)

    panels = [
        FieldPanel('name'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Product Category"
        verbose_name_plural = "Products Categories"


@register_snippet
class PublicationType(models.Model):
    name = models.CharField(max_length=255)
    icon = models.ForeignKey(WebIcon, on_delete=models.PROTECT, blank=True, null=True)

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
        verbose_name_plural = "Publication Types"

@register_snippet
class NewsType(models.Model):
    name = models.CharField(max_length=255)
    is_alert = models.BooleanField(default=False)
    is_press_release = models.BooleanField(default=False)

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
        verbose_name = "News Type"
        verbose_name_plural = "News Types"

@register_snippet
class Application(models.Model):
    title = models.CharField(max_length=100)
    thumbnail = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    url = models.URLField()
    services = models.ManyToManyField(ServiceCategory, through='ServiceApplication', related_name='applications')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

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
        verbose_name = "GIS Application"
        verbose_name_plural = "GIS Applications"


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
    event_type = models.CharField(max_length=255)
    icon = models.ForeignKey(WebIcon, on_delete=models.PROTECT, blank=True, null=True)
    thumbnail = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Thumbnail/image for this type of event."
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


@register_setting(icon='fa-info')
class ImportantPages(BaseSiteSetting):
    mailing_list_signup_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    contact_us_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    all_products_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    all_foodsecuritystatements_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    all_projects_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    all_news_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    all_publications_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    all_videos_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    all_applications_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    all_events_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    all_partners_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    all_tenders_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    all_vacancies_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    all_images_of_change_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    data_center_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    feedback_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    rcc_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    all_weekly_forecasts_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    all_monthly_forecasts_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    all_seasonal_forecasts_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')

    panels = [
        PageChooserPanel('mailing_list_signup_page'),
        PageChooserPanel('contact_us_page'),
        PageChooserPanel('feedback_page'),
        PageChooserPanel('all_weekly_forecasts_page'),
        PageChooserPanel('all_monthly_forecasts_page'),
        PageChooserPanel('all_seasonal_forecasts_page'),
        PageChooserPanel('all_products_page'),
        PageChooserPanel('all_foodsecuritystatements_page'),
        PageChooserPanel('all_projects_page'),
        PageChooserPanel('all_tenders_page'),
        PageChooserPanel('all_vacancies_page'),
        PageChooserPanel('all_news_page'),
        PageChooserPanel('rcc_page'),
        PageChooserPanel('all_publications_page'),
        PageChooserPanel('all_videos_page'),
        PageChooserPanel('all_applications_page'),
        PageChooserPanel('all_events_page'),
        PageChooserPanel('all_partners_page'),
        PageChooserPanel('data_center_page'),
        PageChooserPanel('all_images_of_change_page'),
    ]

