from adminboundarymanager.models import AdminBoundarySettings
from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.template.defaultfilters import truncatechars
from django.urls import reverse
from django.utils import timezone
from django.utils.dates import MONTHS
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from geomanager.models import RasterFileLayer
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from taggit.models import TaggedItemBase
from wagtail import blocks
from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.admin.panels import (FieldPanel, MultiFieldPanel)
from wagtail.api.v2.utils import get_full_url
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.rich_text import RichText
from wagtail.snippets.models import register_snippet
from wagtailmodelchooser import register_model_chooser

from climweb.base.blocks import UUIDModelChooserBlock
from climweb.base.mixins import MetadataPageMixin
from climweb.base.models import Product, ProductItemType
from climweb.base.models import ServiceCategory, AbstractIntroPage
from climweb.base.utils import paginate, query_param_to_list, get_first_non_empty_p_string
from .blocks import (
    ProductItemImageContentBlock,
    ProductItemDocumentContentBlock,
    ProductItemStreamContentBlock
)


class ProductIndexPage(MetadataPageMixin, Page):
    parent_page_types = ['home.HomePage']
    subpage_types = ['products.ProductPage', 'products.SubNationalProductPage']
    template = "subpages_listing.html"
    
    max_count = 1
    is_products_index = True
    
    listing_heading = models.CharField(max_length=255, default="Explore our Products",
                                       verbose_name=_("Products listing Heading"))
    group_menu_items_by_service = models.BooleanField(default=True, verbose_name=_("Group menu items by service"))
    
    content_panels = Page.content_panels + [
        FieldPanel("listing_heading"),
        FieldPanel("group_menu_items_by_service")
    ]
    
    class Meta:
        verbose_name = _('Product Index Page')
        verbose_name_plural = _('Product Index Pages')
    
    @cached_property
    def service_categories(self):
        product_service = set(ProductPage.objects.all().live().values_list('service', flat=True))
        
        unique_services = ServiceCategory.objects.filter(id__in=list(product_service))
        
        return unique_services
    
    @cached_property
    def products_by_service(self):
        services = self.service_categories
        
        products_by_service = {}
        for service in services:
            products_by_service[service] = ProductPage.objects.filter(service=service).live()
        
        return products_by_service
    
    def get_menu_product_pages(self):
        products = ProductPage.objects.live().descendant_of(self).order_by('menu_order')
        subnational_products = SubNationalProductPage.objects.live().descendant_of(self).order_by('menu_order')
        
        return list(products) + list(subnational_products)
    
    def get_meta_image(self):
        meta_image = super().get_meta_image()
        
        if not meta_image:
            meta_image = self.get_parent().get_meta_image()
        
        return meta_image
    
    def get_meta_description(self):
        meta_description = super().get_meta_description()
        
        if not meta_description:
            meta_description = self.get_parent().get_meta_description()
        
        return meta_description


class LayerBlock(blocks.StructBlock):
    geomanager_layer = UUIDModelChooserBlock(RasterFileLayer)
    product_type = blocks.ChoiceBlock(required=False, choices=[])


class ProductPageForm(WagtailAdminPageForm):
    class Media:
        js = ("products/js/product_page_conditional.js",)


class BaseProductPage(AbstractIntroPage):
    base_form_class = ProductPageForm
    
    template = 'products/product_index.html'
    ajax_template = 'product_list_include.html'
    parent_page_types = ['products.ProductIndexPage']
    subpage_types = ['products.ProductItemPage']
    show_in_menus_default = True
    
    service = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT, verbose_name=_("Primary Service"))
    
    products_per_page = models.PositiveIntegerField(default=6, validators=[
        MinValueValidator(6),
        MaxValueValidator(20),
    ], help_text=_("How many of this products should be visible on the landing page filter section ?"),
                                                    verbose_name=_("Products per page"))
    
    default_listing_thumbnail = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name=_("Default Listing Thumbnail"),
        help_text=_("An image that will be used as a thumbnail for in the products listing, "
                    "if no image can be extracted from product items"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    menu_order = models.PositiveIntegerField(default=0, verbose_name=_("Menu Order"))
    
    class Meta:
        abstract = True
    
    @cached_property
    def listing_image(self):
        if self.introduction_image:
            return self.introduction_image
        return None
    
    @cached_property
    def filters(self):
        years = self.all_products.dates("productitempage__date", "year")
        return {'year': years, 'month': MONTHS}
    
    @cached_property
    def all_products(self):
        product_items = self.get_children().specific().live().order_by('-productitempage__date')
        # Return the related items
        return product_items
    
    def filter_products(self, request):
        products = self.all_products
        
        years = query_param_to_list(request.GET.get("year"), as_int=True)
        months = query_param_to_list(request.GET.get("month"), as_int=True)
        
        filters = models.Q()
        
        if years:
            filters &= models.Q(productitempage__date__year__in=years)
        if months:
            filters &= models.Q(productitempage__date__month__in=months)
        
        return products.filter(filters)
    
    def filter_and_paginate_products(self, request):
        page = request.GET.get('page')
        
        filtered_products = self.filter_products(request)
        
        paginated_products = paginate(filtered_products, page, self.products_per_page)
        
        return paginated_products
    
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        
        context['products'] = self.filter_and_paginate_products(request)
        
        return context


class ProductPage(BaseProductPage):
    template = 'products/product_index.html'
    parent_page_types = ['products.ProductIndexPage']
    subpage_types = ['products.ProductItemPage']
    show_in_menus_default = True
    
    product = models.OneToOneField(Product, on_delete=models.PROTECT, verbose_name=_("Product"))
    other_services = ParentalManyToManyField(ServiceCategory, blank=True, verbose_name=_("Other relevant Services"),
                                             related_name="other_services")
    map_layers = StreamField([
        ('layers', LayerBlock(label="Layer"))
    ], blank=True, null=True, use_json_field=True, verbose_name=_("Map Layers"))
    
    content_panels = Page.content_panels + [
        FieldPanel('service'),
        FieldPanel('other_services', widget=forms.CheckboxSelectMultiple),
        FieldPanel('product'),
        *AbstractIntroPage.content_panels,
        MultiFieldPanel(
            [
                FieldPanel('products_per_page'),
                FieldPanel('default_listing_thumbnail'),
                FieldPanel('menu_order'),
            ],
            heading=_("Other settings"),
        ),
    ]
    
    class Meta:
        verbose_name = _('National Product Page')
        verbose_name_plural = _('National Product Pages')
    
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        
        abm_settings = AdminBoundarySettings.for_request(request)
        abm_extents = abm_settings.combined_countries_bounds
        boundary_tiles_url = get_full_url(request, abm_settings.boundary_tiles_url)
        
        context.update({
            "bounds": abm_extents,
            "boundary_tiles_url": boundary_tiles_url
        })
        
        if self.map_layers:
            try:
                context["datasetsurl"] = get_full_url(request, (reverse("datasets-list")))
                context["layertimestampsurl"] = get_full_url(request, reverse("layerrasterfile-list"))
            except Exception:
                pass
        
        return context
    
    @cached_property
    def map_layers_list(self):
        layers = []
        for map_layer in self.map_layers:
            layer = map_layer.value.get("geomanager_layer")
            product_type = map_layer.value.get("product_type")
            
            if product_type:
                product_type = ProductItemType.objects.filter(pk=product_type).first()
            layers.append({
                "layer": layer,
                "product_type": product_type
            })
        return layers


register_model_chooser(RasterFileLayer)


class ProductPageTag(TaggedItemBase):
    content_object = ParentalKey('products.ProductItemPage', on_delete=models.CASCADE, related_name='product_tags',
                                 verbose_name=_("Product Tag"))


class ProductItemPageForm(WagtailAdminPageForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        parent_page = kwargs.get("parent_page")
        products_item_types = parent_page.specific.product.product_item_types
        
        products_field = self.fields.get("products")
        
        for product_content_type, block in products_field.block.child_blocks.items():
            for key, val in block.child_blocks.items():
                if key == "product_type":
                    label = val.label or key
                    products_field.block.child_blocks[product_content_type].child_blocks[key] = blocks.ChoiceBlock(
                        choices=products_item_types)
                    products_field.block.child_blocks[product_content_type].child_blocks[key].name = "product_type"
                    products_field.block.child_blocks[product_content_type].child_blocks[key].label = label
        
        self.fields["products"] = products_field


class ProductItemPage(MetadataPageMixin, Page):
    template = 'products/product_detail.html'
    parent_page_types = ['products.ProductPage', 'products.SubNationalProductPage']
    subpage_types = []
    base_form_class = ProductItemPageForm
    
    date = models.DateField(default=timezone.now, verbose_name=_("Effective from"),
                            help_text=_("The first day when products added below become effective"))
    valid_until = models.DateField(blank=True, null=True, verbose_name=_("Effective until"),
                                   help_text=_("The last day when products added below remain effective. "
                                               "Leave blank if not applicable"))
    products = StreamField([
        ("image_product", ProductItemImageContentBlock(label="Map/Image Product")),
        ("document_product", ProductItemDocumentContentBlock(label="Document/Bulletin Product")),
        ("content_block", ProductItemStreamContentBlock(label="Text/Tabular Product"))
    ], use_json_field=True)
    
    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("valid_until"),
        FieldPanel("products")
    ]
    
    class Meta:
        verbose_name = _("Product Item")
    
    def __str__(self):
        parent_page = self.get_parent().specific
        return f"{parent_page.title} - {self.title}"
    
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        
        parent_page = self.get_parent().specific
        categories = parent_page.product.categories.all()
        product_categories = {}
        
        products_dict = {}
        products = self.products
        for product in products:
            item_type = product.value.product_item_type()
            if not products_dict.get(item_type.slug):
                products_dict[item_type.slug] = {"item_type": item_type, "products": []}
            products_dict[item_type.slug].get("products").append(product)
        context.update({"products": products_dict})
        
        for product_type in products_dict.keys():
            # sort by date
            products_dict[product_type]["products"].sort(key=lambda r: r.value.get("date"))
            
            for category in categories:
                if product_categories.get(category.id):
                    continue
                product_item_types = category.product_item_types.all()
                for item_type in product_item_types:
                    if item_type.slug == product_type:
                        product_categories[category.pk] = category
        
        context.update({"categories": product_categories})
        
        return context
    
    @cached_property
    def product_category(self):
        parent = self.get_parent().specific
        return parent.product.name
    
    @property
    def products_listing_image(self):
        products = self.products
        for product in products:
            if product.value.p_image:
                return product.value.p_image
        
        return None
    
    @property
    def product_listing_description(self):
        products = self.products
        for product in products:
            if product.value.description:
                return product.value.description
        
        return None
    
    def get_meta_image(self):
        meta_image = super().get_meta_image()
        
        if not meta_image:
            meta_image = self.products_listing_image
        
        if not meta_image:
            meta_image = self.get_parent().get_meta_image()
        
        return meta_image
    
    @property
    def listing_summary(self):
        html_description = self.product_listing_description
        if html_description:
            if isinstance(html_description, RichText):
                html = html_description.source
                p = get_first_non_empty_p_string(html)
                if p:
                    # Limit the search meta desc to google's 160 recommended chars
                    return truncatechars(p, 160)
        return None
    
    def get_meta_description(self):
        meta_description = super().get_meta_description()
        
        if not meta_description:
            # try getting from the description of the first product item
            if self.listing_summary:
                meta_description = self.listing_summary
        
        if not meta_description:
            meta_description = self.get_parent().get_meta_description()
        
        return meta_description


@register_snippet
class SubNationalRegion(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Subnational Region')
        verbose_name_plural = _('Subnational Regions')


class SubNationalProductPage(BaseProductPage):
    template = 'products/subnational_product_index.html'
    parent_page_types = ['products.ProductIndexPage']
    subpage_types = ['products.ProductItemPage']
    show_in_menus_default = False
    
    region = models.ForeignKey(SubNationalRegion, on_delete=models.PROTECT, verbose_name=_("Region"))
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_("Product"))
    
    content_panels = Page.content_panels + [
        FieldPanel('region'),
        FieldPanel('service'),
        FieldPanel('product'),
        *AbstractIntroPage.content_panels,
        MultiFieldPanel(
            [
                FieldPanel('products_per_page'),
                FieldPanel('default_listing_thumbnail'),
                FieldPanel('menu_order'),
            ],
            heading=_("Other settings"),
        ),
    ]
    
    class Meta:
        verbose_name = _('Subnational Product Page')
        verbose_name_plural = _('Subnational Product Pages')
