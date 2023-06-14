from django.db import models
from django.forms import CheckboxSelectMultiple
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from positions import PositionField
from wagtail.admin.panels import FieldPanel
from wagtail.admin.panels import InlinePanel
from wagtail.api import APIField
from wagtail.documents.models import Document, document_served
from wagtail.models import Site, Orderable
from wagtail.snippets.models import register_snippet
from wagtail_lazyimages.templatetags.lazyimages_tags import lazy_image_url
from wagtailiconchooser.widgets import IconChooserWidget


class CustomDocumentModel(Document):
    # Custom field
    download_count = models.IntegerField(default=0, blank=True, null=True)


def increment_document_download_count(instance, **kwargs):
    instance.download_count = instance.download_count + 1
    instance.save()


# Count documents download times
document_served.connect(increment_document_download_count)


@register_snippet
class Product(ClusterableModel):
    name = models.CharField(max_length=100, verbose_name=_("Product Name"))

    panels = [
        FieldPanel("name"),
        InlinePanel("categories", heading=_("Product Categories"), label=_("Product Category")),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = _("Product")


class ProductCategory(ClusterableModel):
    product = ParentalKey(Product, on_delete=models.PROTECT, verbose_name=_("Product"), related_name="categories")
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    icon = models.CharField(max_length=100, verbose_name=_("Icon"))

    panels = [
        FieldPanel("product"),
        FieldPanel("name"),
        FieldPanel("icon", widget=IconChooserWidget),
        InlinePanel("product_item_types", heading=_("Product Item Types"), label=_("Product Item Type")),
    ]

    class Meta:
        verbose_name_plural = _("Product Categories")

    def __str__(self):
        return self.name


class ProductItemType(Orderable):
    category = ParentalKey(ProductCategory, on_delete=models.PROTECT, verbose_name=_("Name"),
                           related_name="product_item_types")
    name = models.CharField(max_length=100, verbose_name=_("Name"))

    def __str__(self):
        return self.name

    @cached_property
    def slug(self):
        return slugify(self.name)


@register_snippet
class ServiceCategory(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    icon = models.CharField(max_length=100, null=True, blank=True)

    panels = [
        FieldPanel('name'),
        FieldPanel('icon'),
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
    icon = models.CharField(max_length=100, null=True, blank=True)

    panels = [
        FieldPanel('name'),
        FieldPanel('icon'),
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
    icon = models.CharField(max_length=100, null=True, blank=True)
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
        FieldPanel('icon'),
        FieldPanel('thumbnail'),
    ]

    api_fields = [
        APIField('event_type'),
        APIField('icon'),
    ]

    class Meta:
        verbose_name = _("Event Type")
