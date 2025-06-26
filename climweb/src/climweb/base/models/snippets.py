from django.db import models
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel
from wagtail.admin.panels import InlinePanel
from wagtail.api import APIField
from wagtail.models import Site, Orderable
from wagtail.snippets.models import register_snippet
from wagtail_lazyimages.templatetags.lazyimages_tags import lazy_image_url
from wagtailiconchooser.widgets import IconChooserWidget


@register_snippet
class Product(ClusterableModel):
    name = models.CharField(max_length=100, verbose_name=_("Product Name"))
    
    panels = [
        FieldPanel("name"),
        InlinePanel("categories", heading=_("Product Categories"), label=_("Product Category")),
    ]
    
    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
    
    def __str__(self):
        return self.name
    
    @cached_property
    def product_item_types(self):
        products_item_types = []
        
        categories = self.categories.all()
        
        if categories:
            for category in categories:
                item_types = category.product_item_types.all()
                for item_type in item_types:
                    products_item_types.append((item_type.pk, f"{category.name} - {item_type.name}"))
        
        return products_item_types


class ProductCategory(ClusterableModel):
    product = ParentalKey(Product, on_delete=models.PROTECT, verbose_name=_("Product"), related_name="categories")
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    icon = models.CharField(max_length=100, verbose_name=_("Icon"), default="folder-inverse")
    
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
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["category", "name"], name="unique_category_name")
        ]
    
    def __str__(self):
        return self.name
    
    @cached_property
    def slug(self):
        return slugify(self.name)


class ServiceCategory(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    icon = models.CharField(max_length=100, verbose_name=_("Icon"))
    order = models.IntegerField(null=True, blank=True)
    
    panels = [
        FieldPanel('name'),
        FieldPanel('icon', widget=IconChooserWidget),
        FieldPanel('order'),
    ]
    
    api_fields = [
        APIField('name'),
    ]
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['order']
        verbose_name = _("Service Category")
        verbose_name_plural = _("Service Categories")


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
    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"))
    
    class Meta:
        ordering = ["order"]
        verbose_name = _("Application")
    
    panels = [
        FieldPanel('title'),
        FieldPanel('thumbnail'),
        FieldPanel('url'),
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
