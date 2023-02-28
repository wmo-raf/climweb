from django.db import models
from django.forms import CheckboxSelectMultiple

from wagtail.admin.panels import FieldPanel
from wagtail.api import APIField
from wagtail.models import Site

from cms_pages.webicons.models import WebIcon
from cms_pages.webicons.edit_handlers import WebIconChooserPanel
from positions import PositionField
from wagtail.snippets.models import register_snippet


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

