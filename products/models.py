from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.dates import MONTHS
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail import blocks
from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.admin.panels import (FieldPanel, MultiFieldPanel)
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtailiconchooser.models import CustomIconPage
from wagtailmetadata.models import MetadataPageMixin

from core.models import ServiceCategory, AbstractIntroPage
from core.utils import paginate, query_param_to_list
from core.wagtailsnippets_models import Product
from products.blocks import ProductItemImageContentBlock, ProductItemDocumentContentBlock


class ProductIndexPage(Page):
    parent_page_types = ['home.HomePage']
    subpage_types = ['products.ProductPage']

    max_count = 1

    class Meta:
        verbose_name = _('Product Index Page')
        verbose_name_plural = _('Product Index Pages')


class ProductPage(AbstractIntroPage):
    template = 'product_index.html'
    ajax_template = 'product_list_include.html'
    parent_page_types = ['products.ProductIndexPage']
    subpage_types = ['products.ProductItemPage']
    show_in_menus_default = True

    service = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT, verbose_name=_("Service"))
    product = models.OneToOneField(Product, blank=True, null=True, on_delete=models.PROTECT,
                                   verbose_name=_("Product"))

    products_per_page = models.PositiveIntegerField(default=6, validators=[
        MinValueValidator(6),
        MaxValueValidator(20),
    ], help_text=_("How many of this products should be visible on the landing page filter section ?"),
                                                    verbose_name=_("Products per page"))

    content_panels = Page.content_panels + [
        FieldPanel('service'),
        FieldPanel('product'),
        *AbstractIntroPage.content_panels,
        MultiFieldPanel(
            [
                FieldPanel('products_per_page'),
            ],
            heading=_("Other settings"),
        ),
    ]

    @property
    def filters(self):
        return {'year': [], 'month': MONTHS}

    @property
    def all_products(self):
        product_items = self.get_children().specific().live().order_by('-productitempage__date')
        # Return the related items
        return product_items

    def filter_products(self, request):
        products = self.all_products

        years = query_param_to_list(request.GET.get("year"), as_int=True)
        months = query_param_to_list(request.GET.get("month"), as_int=True)

        filters = models.Q()

        # if years:
        #     filters &= models.Q(year__in=years)
        # if months:
        #     filters &= models.Q(month__in=months)

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
        context = super(ProductPage,
                        self).get_context(request, *args, **kwargs)

        context['products'] = self.filter_and_paginate_products(request)

        return context

    class Meta:
        verbose_name = _('Product Page')
        verbose_name_plural = _('Product Pages')


class ProductPageTag(TaggedItemBase):
    content_object = ParentalKey('products.ProductItemPage', on_delete=models.CASCADE, related_name='product_tags',
                                 verbose_name=_("Product Tag"))


class ProductItemPageForm(WagtailAdminPageForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        parent_page = kwargs.get("parent_page")
        products_item_types = []

        product = parent_page.specific.product

        if product and product.categories:
            for category in product.categories.all():
                item_types = category.product_item_types.all()

                for item_type in item_types:
                    products_item_types.append((item_type.pk, item_type.name))

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


class ProductItemPage(MetadataPageMixin, CustomIconPage, Page):
    template = 'product_detail.html'
    parent_page_types = ['products.ProductPage', ]
    subpage_types = []
    base_form_class = ProductItemPageForm

    date = models.DateField(default=timezone.now, verbose_name=_("Date"))
    valid_until = models.DateField(blank=True, null=True, verbose_name=_("Valid until"),
                                   help_text=_("Up to when is this product valid ? Leave blank if not applicable"))
    products = StreamField([
        ("image_product", ProductItemImageContentBlock(label="Image")),
        ("document_product", ProductItemDocumentContentBlock(label="Document"))
    ], use_json_field=True, blank=True, null=True)

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("valid_until"),
        FieldPanel("products")
    ]

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
            products_dict[item_type.slug] = product
        context.update({"products": products_dict})

        for product_type in products_dict.keys():
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

    class Meta:
        verbose_name = _("Product Item")
