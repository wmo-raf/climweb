from datetime import datetime

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.forms import CheckboxSelectMultiple
from django.template.defaultfilters import truncatechars, date
from django.utils.functional import cached_property
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalManyToManyField, ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, PageChooserPanel
from wagtail.api import APIField
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page
from wagtail.templatetags.wagtailcore_tags import richtext

from core.models import NewsType
from core.utils import paginate, query_param_to_list, get_first_img_src, get_first_non_empty_p_string
from core.wagtailsnippets_models import ServiceCategory
from media_pages.news.blocks import ExternalLinkBlock

NEWS_ALLOWED_RICHTEXT_FEATURES = ['bold', 'italic', 'h4', 'h5', 'h6', 'ol', 'ul', 'hr', 'link', 'image',
                                  'document-link', 'embed', ]


class NewsIndexPage(Page):
    template = 'news_index_page.html'
    parent_page_types = ['home.HomePage']
    subpage_types = ['news.NewsPage']
    max_count = 1
    show_in_menus_default = True

    banner_image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name="Banner Image",
        help_text="A high quality image related to News",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    banner_title = models.CharField(max_length=255)
    banner_subtitle = models.CharField(max_length=255)

    call_to_action_button_text = models.CharField(max_length=100, blank=True, null=True)
    call_to_action_related_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    items_per_page = models.PositiveIntegerField(default=6, validators=[
        MinValueValidator(6),
        MaxValueValidator(20),
    ], help_text="How many items should be visible on the news landing page filter section ?")

    content_panels = Page.content_panels + [
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
                FieldPanel('items_per_page'),

            ],
            heading="Other settings",
        )
    ]

    @cached_property
    def filters(self):
        news_types = NewsType.objects.all()
        service_categories = ServiceCategory.objects.all()
        return {'news_types': news_types, 'service_categories': service_categories, }

    @cached_property
    def featured_news(self):

        queryset = self.all_news.filter()

        featured_news = queryset.filter(is_featured=True).first()

        if featured_news:
            return featured_news
        else:
            featured_news = queryset.first()

        return featured_news

    def filter_news(self, request):
        news = self.all_news

        news_types = query_param_to_list(request.GET.get("news_type"), as_int=True)
        services = query_param_to_list(request.GET.get("service"), as_int=True)

        filters = models.Q()

        if news_types:
            filters &= models.Q(news_type__in=news_types)
        if services:
            filters &= models.Q(services__in=services)

        return news.filter(filters)

    def filter_and_paginate_news(self, request):
        page = request.GET.get('page')

        filtered_news = self.filter_news(request)

        paginated_news = paginate(filtered_news, page, self.items_per_page)

        return paginated_news

    @cached_property
    def all_news(self):
        return NewsPage.objects.live().order_by('-date')

    def get_context(self, request, *args, **kwargs):
        context = super(NewsIndexPage, self).get_context(
            request, *args, **kwargs)

        context['featured_news'] = self.featured_news

        context['news'] = self.filter_and_paginate_news(request)

        return context

    def save(self, *args, **kwargs):
        #if not self.search_image and self.banner_image:
            #self.search_image = self.banner_image
        if not self.search_description and self.banner_subtitle:
            # Limit the search meta desc to google's 160 recommended chars
            self.search_description = truncatechars(self.banner_subtitle, 160)
        return super().save(*args, **kwargs)


class NewsPageTag(TaggedItemBase):
    content_object = ParentalKey('news.NewsPage', on_delete=models.CASCADE,
                                 related_name='news_tags')


class NewsPage(Page):
    template = 'news_detail_page.html'
    parent_page_types = ['news.NewsIndexPage']
    subpage_types = []

    news_type = models.ForeignKey(NewsType, on_delete=models.PROTECT)
    date = models.DateTimeField("Post date", default=datetime.today)
    subtitle = models.TextField(blank=True, null=True, help_text="Optional subtitle")
    body = RichTextField(features=NEWS_ALLOWED_RICHTEXT_FEATURES)
    feature_img_src = models.TextField(blank=True, null=True)
    services = ParentalManyToManyField('core.ServiceCategory', blank=True, verbose_name="Relevant Services")
    projects = ParentalManyToManyField('projects.ProjectPage', blank=True, verbose_name="Relevant Projects")
    is_featured = models.BooleanField(default=False, help_text="Should this news appear on the news landing "
                                                               "paging as the featured one ?")
    is_alert = models.BooleanField(default=False, help_text="Is this an alert ?")
    is_visible_on_homepage = models.BooleanField(default=False,
                                                 help_text="Should this appear in the homepage as"
                                                           " an alert/latest update ?")
    extra_links_heading = models.CharField(max_length=255, blank=True, null=True)

    external_links = StreamField([
        ('link', ExternalLinkBlock())
    ], blank=True, null=True, use_json_field=True)

    tags = ClusterTaggableManager(through=NewsPageTag, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('news_type'),
        FieldPanel('date'),
        FieldPanel('subtitle'),
        FieldPanel('body'),
        FieldPanel('services', widget=CheckboxSelectMultiple),
        FieldPanel('projects', widget=CheckboxSelectMultiple),
        FieldPanel('tags'),

        MultiFieldPanel([
            FieldPanel('extra_links_heading'),
            FieldPanel('external_links'),
        ], heading="Extra Links"),

        FieldPanel('is_featured'),
        FieldPanel('is_alert'),
        FieldPanel('is_visible_on_homepage'),
    ]

    api_fields = [
        APIField('news_type'),
        APIField('date'),
        APIField('subtitle'),
        APIField('services'),
        APIField('projects'),
        APIField('tags'),
        APIField('is_alert'),
    ]

    @cached_property
    def card_props(self):
        card_tags = self.tags.all()

        return {
            "card_image_type": "url",
            "card_image": self.feature_img_src,
            "card_title": self.title,
            "card_text": self.body,
            "card_meta": date(self.date, 'd M Y'),
            "card_more_link": self.url,
            "card_tag": self.news_type,
            "card_tags": card_tags
        }

    def save(self, *args, **kwargs):
        # get the first image src to use as thumbnail
        img_src = get_first_img_src(richtext(self.body))

        if img_src:
            self.feature_img_src = img_src

        if not self.search_description and self.body:
            p = get_first_non_empty_p_string(self.body)
            if p:
                # Limit the search meta desc to google's 160 recommended chars
                self.search_description = truncatechars(p, 160)

        return super().save(*args, **kwargs)