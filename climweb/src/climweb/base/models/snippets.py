from django.db import models
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.admin.panels import FieldPanel
from wagtail.admin.panels import InlinePanel
from wagtail.api import APIField
from wagtail.models import Site, Orderable
from wagtail.snippets.models import register_snippet
from wagtail_lazyimages.templatetags.lazyimages_tags import lazy_image_url
from wagtailiconchooser.widgets import IconChooserWidget


class ProductSnippetForm(WagtailAdminModelForm):
    class Media:
        js = ('base/js/product_ingestion.js',)

TEMPORAL_RESOLUTION_CHOICES = [
    ('yearly', _('Yearly')),
    ('monthly', _('Monthly')),
    ('weekly', _('Weekly')),
    ('daily', _('Daily')),
    ('hourly', _('Hourly')),
    ('dekadal', _('Dekadal')),
    ('pentadal', _('Pentadal')),
]

# Default filename convention patterns per temporal resolution.
# Variables: {yyyy} year, {mm} month, {dd} day, {hh} hour.
TEMPORAL_RESOLUTION_DEFAULT_CONVENTIONS = {
    'yearly': '{yyyy}_01_01_00_00_00',
    'monthly': '{yyyy}_{mm}_01_00_00_00',
    'weekly': '{yyyy}_{mm}_{dd}_00_00_00',
    'daily': '{yyyy}_{mm}_{dd}_00_00_00',
    'hourly': '{yyyy}_{mm}_{dd}_{hh}_00_00',
    'dekadal': '{yyyy}_{mm}_{dd}_00_00_00',
    'pentadal': '{yyyy}_{mm}_{dd}_00_00_00',
}

IMAGE_FORMATS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'tiff', 'bmp'}
DOCUMENT_FORMATS = {'pdf', 'docx', 'doc', 'xlsx', 'xls', 'pptx', 'ppt', 'csv', 'txt', 'zip'}


@register_snippet
class Product(ClusterableModel):
    base_form_class = ProductSnippetForm

    name = models.CharField(max_length=100, verbose_name=_("Product Name"))
    variable_name = models.SlugField(
        max_length=100,
        blank=True,
        verbose_name=_("Variable Name"),
        help_text=_("Folder name for this product, e.g. 'daily_forecast'. "
                    "Used as the top-level folder in the watch root path."),
    )
    temporal_resolution = models.CharField(
        max_length=20,
        choices=TEMPORAL_RESOLUTION_CHOICES,
        blank=True,
        verbose_name=_("Temporal Resolution"),
        help_text=_("Determines the default filename date convention for product item types."),
    )
    watch_root = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Watch Root Path"),
        help_text=_("Path containing the {variable_name} folder. "
                    "Relative paths are resolved from MEDIA_ROOT (e.g. 'products'). "
                    "Full scan path: {watch_root}/{variable_name}/{format}/{name_convention}.{format}"),
    )
    ingestion_enabled = models.BooleanField(
        default=False,
        verbose_name=_("Enable Auto-Ingestion"),
        help_text=_("When enabled, the system will periodically scan the watch root for new files."),
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("ingestion_enabled"),
        FieldPanel("variable_name"),
        FieldPanel("temporal_resolution"),
        FieldPanel("watch_root"),
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

    def get_default_convention(self):
        return TEMPORAL_RESOLUTION_DEFAULT_CONVENTIONS.get(self.temporal_resolution, '')


class ProductCategory(ClusterableModel):
    product = ParentalKey(Product, on_delete=models.PROTECT, verbose_name=_("Product"), related_name="categories")
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    icon = models.CharField(max_length=100, verbose_name=_("Icon"), default="folder-inverse")
    category_format = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("File Format"),
        help_text=_("The file format/extension for this category, e.g. 'png', 'pdf', 'jpg'. "
                    "This also determines the subfolder name: {variable_name}/{format}/"),
    )

    panels = [
        FieldPanel("product"),
        FieldPanel("name"),
        FieldPanel("icon", IconChooserWidget),
        FieldPanel("category_format"),
        InlinePanel("product_item_types", heading=_("Product Item Types"), label=_("Product Item Type")),
    ]

    class Meta:
        verbose_name_plural = _("Product Categories")

    def __str__(self):
        return self.name

    @property
    def is_image_format(self):
        return self.category_format.lower() in IMAGE_FORMATS

    @property
    def is_document_format(self):
        return self.category_format.lower() in DOCUMENT_FORMATS


class ProductItemType(Orderable):
    category = ParentalKey(ProductCategory, on_delete=models.PROTECT, verbose_name=_("Name"),
                           related_name="product_item_types")
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    file_name_convention = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Filename Convention"),
        help_text=_(
            "Filename pattern used to match and parse product files (without extension). "
            "Use {yyyy} for year, {mm} for month, {dd} for day, {hh} for hour. "
            "Auto-populated from the product temporal resolution. "
            "You may add a prefix or suffix, e.g. 'temp_{yyyy}_{mm}_{dd}_00_00_00'."
        ),
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["category", "name"], name="unique_category_name")
        ]

    def __str__(self):
        return self.name

    @cached_property
    def slug(self):
        return slugify(self.name)

    def save(self, *args, **kwargs):
        if not self.file_name_convention:
            try:
                temporal_resolution = self.category.product.temporal_resolution
                self.file_name_convention = TEMPORAL_RESOLUTION_DEFAULT_CONVENTIONS.get(temporal_resolution, '')
            except Exception:
                pass
        super().save(*args, **kwargs)


class ServiceCategory(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    icon = models.CharField(max_length=100, verbose_name=_("Icon"))
    order = models.IntegerField(null=True, blank=True)
    
    panels = [
        FieldPanel('name'),
        FieldPanel('icon', IconChooserWidget),
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
