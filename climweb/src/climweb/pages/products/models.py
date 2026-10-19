from collections import Counter

from adminboundarymanager.models import AdminBoundary, AdminBoundarySettings
from django import forms
from django.contrib.gis.db.models import Extent
from django.contrib.gis.db.models.functions import PointOnSurface
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.template.defaultfilters import truncatechars
from django.urls import reverse
from django.utils import timezone
from django.utils.dates import MONTHS
from django.utils.functional import cached_property
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from geomanager.models import RasterFileLayer
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from taggit.models import TaggedItemBase
from wagtail import blocks
from wagtail.admin.forms import WagtailAdminModelForm, WagtailAdminPageForm
from wagtail.admin.panels import (FieldPanel, MultiFieldPanel)
from wagtail.api.v2.utils import get_full_url
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.rich_text import RichText
from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail.snippets.models import register_snippet
from climweb.base.choosers import register_searchable_chooser

from climweb.base.blocks import UUIDModelChooserBlock
from climweb.base.mixins import MetadataPageMixin
from climweb.base.models import Product, ProductItemType
from climweb.base.models import ServiceCategory, AbstractIntroPage
from climweb.base.utils import paginate, query_param_to_list, get_first_non_empty_p_string
from climweb.pages.publications.models import PageView
from .subnational import boundary_svg, querystring
from .blocks import (
    ProductItemImageContentBlock,
    ProductItemDocumentContentBlock,
    ProductItemGifContentBlock,
    ProductItemStreamContentBlock
)


class ProductIndexPage(MetadataPageMixin, Page):
    parent_page_types = ['home.HomePage']
    subpage_types = [
        'products.ProductPage',
        'products.SubNationalProductsLandingPage'
    ]
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
            parent = self.get_parent()
            if hasattr(parent, 'get_meta_image'):
                meta_image = parent.get_meta_image()
        
        return meta_image
    
    def get_meta_description(self):
        meta_description = super().get_meta_description()
        
        if not meta_description:
            parent = self.get_parent()
            # get from homepage
            if hasattr(parent, 'get_meta_description'):
                meta_description = parent.get_meta_description()
        
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

    audio_playlists = StreamField(
        [
            ('playlist', SnippetChooserBlock('audio.AudioPlaylist', label=_("Audio playlist"))),
        ],
        null=True, blank=True, verbose_name=_("Audio playlists"),
        help_text=_("Playlists or podcasts from SoundCloud, YouTube Music, Spotify, Apple Podcasts or an RSS feed"))
    
    content_panels = Page.content_panels + [
        FieldPanel('service'),
        FieldPanel('other_services', widget=forms.CheckboxSelectMultiple),
        FieldPanel('product'),
        *AbstractIntroPage.content_panels,
        FieldPanel('audio_playlists'),
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
    
    @property
    def view_count(self):
        """Get the total number of views for this product page"""
        try:
            from django.contrib.contenttypes.models import ContentType
            content_type = ContentType.objects.get_for_model(self)
            return PageView.objects.filter(content_type=content_type, object_id=self.pk).count()
        except Exception:
            return 0
    
    def record_view(self, request=None, **kwargs):
        """Record a view of this product page"""
        try:
            view_record = PageView.record_view(self, request=request, **kwargs)
            return view_record
        except Exception as e:
            print(f"Error in record_view for ProductPage: {e}")
            return None

    def serve(self, request, *args, **kwargs):
        """Override serve to record page views when the product page is accessed"""
        try:
            # Only record views for GET requests from non-authenticated users and not in preview mode
            if (request.method == 'GET' and 
                not request.user.is_authenticated and 
                not getattr(request, 'is_preview', False)):
                
                # Check if internal tracking is enabled in settings
                from climweb.base.models import IntegrationSettings
                try:
                    integration_settings = IntegrationSettings.for_request(request)
                    if integration_settings and integration_settings.track_internally:
                        self.record_view(request)
                except Exception:
                    # If settings are not available, don't track views
                    pass
        except Exception as e:
            # Log the error for debugging but continue serving the page
            print(f"Error recording page view: {e}")
        
        return super().serve(request, *args, **kwargs)


register_searchable_chooser(RasterFileLayer)


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
        ("gif_product", ProductItemGifContentBlock(label="GIF Product")),
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
        categories = list(parent_page.product.categories.all())

        # build a complete map: item_type_id → list of category ids
        # (one item type can belong to multiple categories)
        item_type_to_categories = {}
        for category in categories:
            for item_type in category.product_item_types.all():
                if item_type.pk not in item_type_to_categories:
                    item_type_to_categories[item_type.pk] = []
                item_type_to_categories[item_type.pk].append(category.id)

        product_categories = {}
        products_dict = {}

        for product in self.products:
            item_type = product.value.product_item_type()

            # find which category this item type belongs to
            category_ids = item_type_to_categories.get(item_type.pk, [])
            # use the first matching category — or None
            category_id = category_ids[0] if category_ids else None

            # composite key guarantees uniqueness across categories
            composite_key = f"{category_id}-{item_type.pk}" if category_id else str(item_type.pk)

            if composite_key not in products_dict:
                products_dict[composite_key] = {
                    "item_type": item_type,
                    "category_id": category_id,
                    "products": [],
                }
            products_dict[composite_key]["products"].append(product)

            # collect categories that have products
            if category_id and category_id not in product_categories:
                for cat in categories:
                    if cat.id == category_id:
                        product_categories[cat.id] = cat
                        break

        # sort each group by date
        for key in products_dict:
            products_dict[key]["products"].sort(key=lambda r: r.value.get("date"))

        context.update({
            "products": products_dict,
            "categories": product_categories,
        })

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
            parent = self.get_parent()
            if hasattr(parent, 'get_meta_image'):
                meta_image = parent.get_meta_image()
        
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
            parent = self.get_parent()
            if hasattr(parent, 'get_meta_description'):
                meta_description = parent.get_meta_description()
        
        return meta_description
    
    @property
    def view_count(self):
        """Get the total number of views for this product item page"""
        try:
            from django.contrib.contenttypes.models import ContentType
            content_type = ContentType.objects.get_for_model(self)
            return PageView.objects.filter(content_type=content_type, object_id=self.pk).count()
        except Exception:
            return 0
    
    def record_view(self, request=None, **kwargs):
        """Record a view of this product item page"""
        try:
            view_record = PageView.record_view(self, request=request, **kwargs)
            return view_record
        except Exception as e:
            print(f"Error in record_view for ProductItemPage: {e}")
            return None

    def serve(self, request, *args, **kwargs):
        """Override serve to record page views when the product item page is accessed"""
        try:
            # Only record views for GET requests from non-authenticated users and not in preview mode
            if (request.method == 'GET' and 
                not request.user.is_authenticated and 
                not getattr(request, 'is_preview', False)):
                
                # Check if internal tracking is enabled in settings
                from climweb.base.models import IntegrationSettings
                try:
                    integration_settings = IntegrationSettings.for_request(request)
                    if integration_settings and integration_settings.track_internally:
                        self.record_view(request)
                except Exception:
                    # If settings are not available, don't track views
                    pass
        except Exception as e:
            # Log the error for debugging but continue serving the page
            print(f"Error recording page view: {e}")
        
        return super().serve(request, *args, **kwargs)


class ProductIngestedFile(models.Model):
    """Tracks files that have already been auto-ingested to prevent duplicates."""
    product = models.ForeignKey(
        'base.Product',
        on_delete=models.CASCADE,
        related_name='ingested_files',
        verbose_name=_("Product"),
    )
    file_path = models.CharField(max_length=1000, verbose_name=_("File Path"))
    file_mtime = models.FloatField(verbose_name=_("File Modification Time"))
    product_item_page = models.ForeignKey(
        ProductItemPage,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ingested_files',
        verbose_name=_("Product Item Page"),
    )
    ingested_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Ingested At"))

    class Meta:
        unique_together = [('product', 'file_path')]
        verbose_name = _("Product Ingested File")
        verbose_name_plural = _("Product Ingested Files")

    def __str__(self):
        return self.file_path


class SubNationalProductsLandingPage(AbstractIntroPage, Page):
    parent_page_types = ['products.ProductIndexPage']
    subpage_types = ['products.SubNationalProductPage']
    template = "products/subnational/subnational_products_landing.html"
    
    max_count = 1
    
    admin_level_1_name = models.CharField(
        max_length=100, default="District", verbose_name=_("Admin level 1 name"),
        help_text=_("What admin level 1 boundaries are called in this country, e.g. Region, Province, County"))
    admin_level_2_name = models.CharField(
        max_length=100, default="Sub-district", verbose_name=_("Admin level 2 name"),
        help_text=_("What admin level 2 boundaries are called in this country, e.g. District, Sub-county"))
    
    content_panels = Page.content_panels + AbstractIntroPage.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("admin_level_1_name"),
                FieldPanel("admin_level_2_name"),
            ],
            heading=_("Admin boundary level names"),
        ),
    ]
    
    class Meta:
        verbose_name = _('Subnational Product Landing Page')
        verbose_name_plural = _('Subnational Product Landing Pages')
    
    @cached_property
    def all_items(self):
        product_pages = self.get_children().specific().live()
        return product_pages
    
    @cached_property
    def product_pages(self):
        return SubNationalProductPage.objects.live().child_of(self)
    
    @cached_property
    def boundary_index(self):
        """
        Districts (admin level 1) and sub-districts (admin level 2) that have live products, with
        product counts and a label point for the map. Districts are included when only their
        sub-districts have products.
        """
        linked = self.product_pages.filter(region__admin_level__isnull=False, region__admin_gid__isnull=False) \
            .values_list("region__admin_level", "region__admin_gid", "region__name")
        counts = Counter((level, gid) for level, gid, _name in linked)
        # regions can be named differently from the boundary data, e.g. "Nkhata Bay" for "Nkhatabay"
        region_names = {(level, gid): name for level, gid, name in linked}
        
        sub_districts = {}
        for boundary in AdminBoundary.objects.filter(level=2, gid_2__in=[g for (l, g) in counts if l == 2]) \
                .annotate(label_point=PointOnSurface("geom")):
            sub_districts[boundary.gid_2] = {
                "gid": boundary.gid_2,
                "name": region_names.get((2, boundary.gid_2), boundary.name_2),
                "district_gid": boundary.gid_1,
                "count": counts[(2, boundary.gid_2)],
                "point": boundary.label_point.coords,
            }
        
        district_gids = {g for (l, g) in counts if l == 1} | {s["district_gid"] for s in sub_districts.values()}
        
        districts = {}
        for boundary in AdminBoundary.objects.filter(level=1, gid_1__in=district_gids) \
                .annotate(label_point=PointOnSurface("geom")):
            districts[boundary.gid_1] = {
                "gid": boundary.gid_1,
                "name": region_names.get((1, boundary.gid_1), boundary.name_1),
                "count": counts[(1, boundary.gid_1)],
                "point": boundary.label_point.coords,
                "sub_districts": [],
            }
        
        for sub_district in sorted(sub_districts.values(), key=lambda s: s["name"]):
            district = districts.get(sub_district["district_gid"])
            if district:
                district["sub_districts"].append(sub_district)
                district["count"] += sub_district["count"]
        
        districts = dict(sorted(districts.items(), key=lambda d: d[1]["name"]))
        
        return {"districts": districts, "sub_districts": sub_districts}
    
    @cached_property
    def filters(self):
        """
        Districts with their sub-districts nested, built from the boundaries linked to the product
        pages' regions. Regions without a boundary are listed separately.
        """
        region_counts = Counter(
            self.product_pages.filter(region__admin_gid__isnull=True).values_list("region", flat=True)
        )
        other_regions = [
            {"id": region.id, "name": region.name, "count": region_counts[region.id]}
            for region in SubNationalRegion.objects.filter(id__in=region_counts).order_by("name")
        ]
        
        return {
            "districts": list(self.boundary_index["districts"].values()),
            "other_regions": other_regions,
        }
    
    def get_selection(self, request):
        return {
            "districts": query_param_to_list(request.GET.get("district")) or [],
            "sub_districts": query_param_to_list(request.GET.get("subdistrict")) or [],
            "regions": query_param_to_list(request.GET.get("region"), as_int=True) or [],
        }
    
    def filter_items(self, request):
        items = self.all_items
        selection = self.get_selection(request)
        districts, sub_districts, regions = selection["districts"], selection["sub_districts"], selection["regions"]
        
        if not districts and not sub_districts and not regions:
            return items
        
        filters = models.Q()
        
        # a selected sub-district narrows down its district
        if sub_districts:
            filters |= models.Q(subnationalproductpage__region__admin_level=2,
                                subnationalproductpage__region__admin_gid__in=sub_districts)
        elif districts:
            district_sub_districts = AdminBoundary.objects.filter(level=2, gid_1__in=districts) \
                .values_list("gid_2", flat=True)
            filters |= models.Q(subnationalproductpage__region__admin_level=1,
                                subnationalproductpage__region__admin_gid__in=districts)
            filters |= models.Q(subnationalproductpage__region__admin_level=2,
                                subnationalproductpage__region__admin_gid__in=list(district_sub_districts))
        
        if regions:
            filters |= models.Q(subnationalproductpage__region__id__in=regions)
        
        return items.filter(filters)
    
    def filter_and_paginate_items(self, request):
        page = request.GET.get('page')
        
        filtered_products = self.filter_items(request)
        
        paginated_products = paginate(filtered_products, page, 10)
        
        return paginated_products
    
    def get_active_filters(self, request):
        """Chips for the current selection, each with a link that removes it"""
        selection = self.get_selection(request)
        index = self.boundary_index
        chips = []
        
        for gid in selection["districts"]:
            district = index["districts"].get(gid)
            if district:
                chips.append({"label": district["name"],
                              "url": querystring(request, district=None, subdistrict=None)})
        
        for gid in selection["sub_districts"]:
            sub_district = index["sub_districts"].get(gid)
            if sub_district:
                chips.append({"label": sub_district["name"], "url": querystring(request, subdistrict=None)})
        
        regions = {r["id"]: r for r in self.filters["other_regions"]}
        for region_id in selection["regions"]:
            if region_id in regions:
                chips.append({"label": regions[region_id]["name"], "url": querystring(request, region=None)})
        
        return chips
    
    def get_map_config(self, request):
        index = self.boundary_index
        
        if not index["districts"]:
            return None
        
        selection = self.get_selection(request)
        
        # zoom to the selection if there is one, otherwise to all areas with products
        if selection["districts"] or selection["sub_districts"]:
            area = models.Q(level=1, gid_1__in=selection["districts"]) | \
                   models.Q(level=2, gid_2__in=selection["sub_districts"])
        else:
            area = models.Q(level=1, gid_1__in=list(index["districts"])) | \
                   models.Q(level=2, gid_2__in=list(index["sub_districts"]))
        
        extent = AdminBoundary.objects.filter(area).aggregate(extent=Extent("geom"))["extent"]
        abm_settings = AdminBoundarySettings.for_request(request)
        
        def label(area, level):
            return {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": area["point"]},
                "properties": {"name": area["name"], "count": area["count"], "level": level},
            }
        
        labels = [label(d, 1) for d in index["districts"].values()] + \
                 [label(s, 2) for s in index["sub_districts"].values()]
        
        return {
            "boundaryTilesUrl": get_full_url(request, abm_settings.boundary_tiles_url),
            "bounds": list(extent) if extent else abm_settings.combined_countries_bounds,
            "districts": list(index["districts"]),
            "subDistricts": list(index["sub_districts"]),
            "selectedDistricts": selection["districts"],
            "selectedSubDistricts": selection["sub_districts"],
            "labels": {"type": "FeatureCollection", "features": labels},
        }
    
    def get_location(self, region):
        """The district and sub-district a region is linked to, if any"""
        index = self.boundary_index
        location = {"district": None, "sub_district": None}
        
        if region.admin_level == 1:
            location["district"] = index["districts"].get(region.admin_gid)
        elif region.admin_level == 2:
            location["sub_district"] = index["sub_districts"].get(region.admin_gid)
            if location["sub_district"]:
                location["district"] = index["districts"].get(location["sub_district"]["district_gid"])
        
        return location
    
    def add_listing_details(self, product_pages):
        """Location, latest update and a boundary outline thumbnail for each listed product page"""
        for product_page in product_pages:
            region = product_page.region
            product_page.location = self.get_location(region)
            product_page.latest_update = ProductItemPage.objects.live().child_of(product_page) \
                .aggregate(latest=models.Max("date"))["latest"]
            
            product_page.boundary_thumbnail = None
            if not product_page.introduction_image and not product_page.default_listing_thumbnail:
                boundary = region.boundary
                if boundary:
                    product_page.boundary_thumbnail = boundary_svg(boundary.geom)
    
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        
        items = self.filter_and_paginate_items(request)
        self.add_listing_details(items)
        
        selection = self.get_selection(request)
        selected_district = self.boundary_index["districts"].get(next(iter(selection["districts"]), None))
        
        context.update({
            "items": items,
            "map_config": self.get_map_config(request),
            "selection": selection,
            "selected_district": selected_district,
            "active_filters": self.get_active_filters(request),
            # hide the introduction text when it only repeats the title
            "show_introduction_text": strip_tags(str(self.introduction_text or "")).strip()
                                      != (self.introduction_title or "").strip(),
        })
        
        return context


class SubNationalRegionForm(WagtailAdminModelForm):
    admin_boundary = forms.ChoiceField(
        required=False,
        label=_("Admin boundary"),
        help_text=_("Optional. The admin boundary this region matches. Used to browse products by area "
                    "and on the map. Leave empty for regions that do not match a single boundary."),
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        landing_page = SubNationalProductsLandingPage.objects.first()
        if landing_page:
            level_1_name, level_2_name = landing_page.admin_level_1_name, landing_page.admin_level_2_name
        else:
            level_1_name, level_2_name = _("Admin level 1"), _("Admin level 2")
        
        level_1_names = dict(AdminBoundary.objects.filter(level=1).values_list("gid_1", "name_1"))
        level_1 = sorted(level_1_names.items(), key=lambda b: b[1] or "")
        level_2 = AdminBoundary.objects.filter(level=2).order_by("name_1", "name_2") \
            .values_list("gid_1", "gid_2", "name_1", "name_2")
        
        self.fields["admin_boundary"].choices = [
            ("", "---------"),
            (f"{level_1_name} ({_('admin level 1')})", [(f"1:{gid}", name) for gid, name in level_1]),
            (f"{level_2_name} ({_('admin level 2')})", [
                (f"2:{gid_2}", f"{level_1_names.get(gid_1, name_1)} › {name_2}")
                for gid_1, gid_2, name_1, name_2 in level_2
            ]),
        ]
        
        if self.instance.admin_level and self.instance.admin_gid:
            self.initial["admin_boundary"] = f"{self.instance.admin_level}:{self.instance.admin_gid}"
    
    def save(self, commit=True):
        value = self.cleaned_data.get("admin_boundary")
        
        if value:
            level, gid = value.split(":", 1)
            self.instance.admin_level = int(level)
            self.instance.admin_gid = gid
        else:
            self.instance.admin_level = None
            self.instance.admin_gid = None
        
        return super().save(commit=commit)


@register_snippet
class SubNationalRegion(models.Model):
    base_form_class = SubNationalRegionForm
    
    ADMIN_LEVEL_CHOICES = (
        (1, _("Admin level 1")),
        (2, _("Admin level 2")),
    )
    
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    # Stored as boundary codes rather than a foreign key, because reloading boundary data
    # deletes and recreates AdminBoundary rows.
    admin_level = models.PositiveSmallIntegerField(blank=True, null=True, choices=ADMIN_LEVEL_CHOICES,
                                                   verbose_name=_("Admin level"))
    admin_gid = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Admin boundary code"))
    
    panels = [
        FieldPanel("name"),
        FieldPanel("admin_boundary"),
    ]
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Subnational Region')
        verbose_name_plural = _('Subnational Regions')
    
    @cached_property
    def boundary(self):
        if not self.admin_level or not self.admin_gid:
            return None
        return AdminBoundary.objects.filter(level=self.admin_level,
                                            **{f"gid_{self.admin_level}": self.admin_gid}).first()


class SubNationalProductPage(BaseProductPage):
    template = 'products/subnational/subnational_product_index.html'
    parent_page_types = ['products.SubNationalProductsLandingPage']
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
    
    @cached_property
    def listing_summary(self):
        summary = self.get_meta_description()
        return summary
    
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        
        landing_page = self.get_parent().specific
        region = self.region
        boundary = region.boundary
        
        if region.admin_level == 2:
            area_name = landing_page.admin_level_2_name
        elif region.admin_level == 1:
            area_name = landing_page.admin_level_1_name
        else:
            area_name = _("Region")
        
        # the same product for other areas, to switch between them
        other_areas = SubNationalProductPage.objects.live().sibling_of(self) \
            .filter(product_id=self.product_id).select_related("region").order_by("region__name")
        
        context.update({
            "landing_page": landing_page,
            "location": landing_page.get_location(region),
            "area_name": area_name,
            "other_areas": other_areas if other_areas.count() > 1 else None,
            "boundary_thumbnail": boundary_svg(boundary.geom) if boundary else None,
            "latest_update": self.all_products.aggregate(latest=models.Max("productitempage__date"))["latest"],
            "has_updates": self.all_products.exists(),
            # hide the introduction text when it only repeats a title
            "show_introduction_text": strip_tags(str(self.introduction_text or "")).strip()
                                      not in ((self.introduction_title or "").strip(), self.title.strip()),
        })
        
        return context
    
    @property
    def view_count(self):
        """Get the total number of views for this subnational product page"""
        try:
            from django.contrib.contenttypes.models import ContentType
            content_type = ContentType.objects.get_for_model(self)
            return PageView.objects.filter(content_type=content_type, object_id=self.pk).count()
        except Exception:
            return 0
    
    def record_view(self, request=None, **kwargs):
        """Record a view of this subnational product page"""
        try:
            view_record = PageView.record_view(self, request=request, **kwargs)
            return view_record
        except Exception as e:
            print(f"Error in record_view for SubNationalProductPage: {e}")
            return None

    def serve(self, request, *args, **kwargs):
        """Override serve to record page views when the subnational product page is accessed"""
        try:
            # Only record views for GET requests from non-authenticated users and not in preview mode
            if (request.method == 'GET' and 
                not request.user.is_authenticated and 
                not getattr(request, 'is_preview', False)):
                
                # Check if internal tracking is enabled in settings
                from climweb.base.models import IntegrationSettings
                try:
                    integration_settings = IntegrationSettings.for_request(request)
                    if integration_settings and integration_settings.track_internally:
                        self.record_view(request)
                except Exception:
                    # If settings are not available, don't track views
                    pass
        except Exception as e:
            # Log the error for debugging but continue serving the page
            print(f"Error recording page view: {e}")
        
        return super().serve(request, *args, **kwargs)


# Registered with this app so migrations live alongside the other product
# models. See sync_models.py for what these do.
from .sync_models import ProductSyncCredential, ProductSyncSetupCode  # noqa: E402,F401
