import calendar
from datetime import datetime

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.template.defaultfilters import truncatechars
from django.utils.dates import MONTHS
from django.utils.functional import cached_property
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import (FieldPanel, MultiFieldPanel, PageChooserPanel)
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page

from core import blocks
from core.models import ProductCategory, ServiceCategory
from core.utils import get_years, paginate, query_param_to_list, get_first_non_empty_p_string
from nmhs_cms.settings.base import SUMMARY_RICHTEXT_FEATURES

class ProductIndexPage(Page):

    parent_page_types = ['home.HomePage']
    subpage_types = ['products.ProductPage']

    max_count = 1

    class Meta:
        verbose_name = 'Product Page'
        verbose_name_plural = 'Product Pages'

class ProductPage(Page):
    template = 'product_index.html'
    ajax_template = 'product_list_include.html'
    parent_page_types = ['products.ProductIndexPage']
    subpage_types = ['products.ProductItemPage']
    # max_count = 1
    show_in_menus_default = True

    service = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT)
    product = models.OneToOneField(ProductCategory, on_delete=models.PROTECT)

    banner_image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name="Banner Image",
        help_text="A high quality image related to this Product",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    banner_title = models.CharField(max_length=255)
    banner_subtitle = models.CharField(max_length=255, blank=True, null=True)

    call_to_action_button_text = models.CharField(max_length=100, blank=True, null=True)
    call_to_action_related_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    introduction_title = models.CharField(max_length=100, help_text="Introduction section title")
    introduction_text = RichTextField(help_text="A description of what your organisation does under  this Product",
                                      features=SUMMARY_RICHTEXT_FEATURES)
    introduction_image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name="Introduction Image",
        help_text="A high quality image related to this Product",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    introduction_button_text = models.TextField(max_length=20, blank=True, null=True)
    introduction_button_link = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    feature_block = StreamField([
        ('feature_item', blocks.FeatureBlock()),
    ], null=True, blank=True, use_json_field=True)

    earliest_bulletin_year = models.PositiveIntegerField(
        default=datetime.now().year,
        validators=[
            MinValueValidator(2000),
            MaxValueValidator(datetime.now().year),
        ],
        help_text="The year for the earliest available bulletin. This is used to generate the years available for "
                  "filtering ")
    products_per_page = models.PositiveIntegerField(default=6, validators=[
        MinValueValidator(6),
        MaxValueValidator(20),
    ], help_text="How many of this products should be visible on the landing page filter section ?")

    content_panels = Page.content_panels + [
        FieldPanel('service'),
        FieldPanel('product'),
        MultiFieldPanel(
            [
                FieldPanel('banner_image'),
                FieldPanel('banner_title'),
                FieldPanel('banner_subtitle'),
                FieldPanel('call_to_action_button_text'),
                PageChooserPanel('call_to_action_related_page', )

            ],
            heading="Banner Section",
        ),
        MultiFieldPanel(
            [
                FieldPanel('introduction_title'),
                FieldPanel('introduction_image'),
                FieldPanel('introduction_text'),
                FieldPanel('introduction_button_text'),
                PageChooserPanel('introduction_button_link'),
            ],
            heading=" Introduction Section",
        ),
        FieldPanel('feature_block'),
        MultiFieldPanel(
            [
                FieldPanel('earliest_bulletin_year'),
                FieldPanel('products_per_page'),
            ],
            heading="Other settings",
        ),
    ]

    @property
    def filters(self):
        return {'year': get_years(self.earliest_bulletin_year), 'month': MONTHS}

    @property
    def all_products(self):

        product_items = self.get_children().specific().live().order_by('-productitempage__year', '-productitempage__month')
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
            filters &= models.Q(productitempage__year__in=years)
        if months:
            filters &= models.Q(productitempage__month__in=months)

        return products.filter(filters)

    def filter_and_paginate_products(self, request):
        page = request.GET.get('page')

        filtered_products = self.filter_products(request)

        paginated_products = paginate(filtered_products, page, self.products_per_page)

        return paginated_products

    # @cached_property
    # def latest_updates(self):
    #     return CropMonitorDetailPage.objects.live().order_by('-year', '-month')[:4]

    def get_context(self, request, *args, **kwargs):
        context = super(ProductPage,
                        self).get_context(request, *args, **kwargs)

        context['products'] = self.filter_and_paginate_products(request)

        return context

    def save(self, *args, **kwargs):
        #if not self.search_image and self.banner_image:
            #self.search_image = self.banner_image
        if not self.search_description and self.introduction_text:
            p = get_first_non_empty_p_string(self.introduction_text)
            if p:
                # Limit the search meta desc to google's 160 recommended chars
                self.search_description = truncatechars(p, 160)
        return super().save(*args, **kwargs)


class ProductPageTag(TaggedItemBase):
    content_object = ParentalKey('products.ProductItemPage', on_delete=models.CASCADE,
                                 related_name='product_tags')


class ProductItemPage(Page):
    template = 'product_detail.html'
    parent_page_types = ['products.ProductPage', ]
    subpage_types = []

    year = models.PositiveIntegerField(default=datetime.now().year, choices=get_years(2010, True))
    month = models.IntegerField(choices=MONTHS.items(), default=datetime.now().month)
    summary = RichTextField(help_text="Summary of the product release", features=SUMMARY_RICHTEXT_FEATURES)
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Image that will appear as thumbnail"
    )
    document = models.ForeignKey(
        'core.CustomDocumentModel',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    tags = ClusterTaggableManager(through=ProductPageTag, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('year'),
        FieldPanel('month'),
        FieldPanel('summary'),
        FieldPanel('image'),
        FieldPanel('document'),
        FieldPanel('tags'),
    ]

    @cached_property
    def product_category(self):
        parent = self.get_parent().specific
        return parent.product.name

    @cached_property
    def period(self):
        return '{} {}'.format(calendar.month_name[self.month], self.year)

    @cached_property
    def card_props(self):
        card_file = {
            "size": self.document.file_size,
            "url": self.document.url,
            "downloads": self.document.download_count
        }
        card_tags = self.tags.all()

        return {
            "card_image": self.image,
            "card_title": self.title,
            "card_text": self.summary,
            "card_meta": self.period,
            "card_more_link": self.url,
            "card_tag": self.product_category,
            "card_file": card_file,
            "card_tags": card_tags,
            # "card_views": self.webhits.count,
            "card_ga_label": self.product_category
        }

    @cached_property
    def related_items(self):
        related_items = ProductItemPage.objects.live().exclude(pk=self.pk)[:3]
        return related_items

    def get_context(self, request, *args, **kwargs):
        context = super(ProductItemPage, self).get_context(request, *args, **kwargs)

        context['related_items'] = self.related_items

        return context

    class Meta:
        verbose_name = "Product Bulletin"

    def save(self, *args, **kwargs):
        # if not self.search_image and self.image:
        #     self.search_image = self.image
        if not self.search_description and self.summary:
            p = get_first_non_empty_p_string(self.summary)
            if p:
                # Limit the search meta desc to google's 160 recommended chars
                self.search_description = truncatechars(p, 160)
        return super().save(*args, **kwargs)