from datetime import datetime

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.forms import CheckboxSelectMultiple
from django.template.defaultfilters import truncatechars, date
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalManyToManyField, ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.api import APIField
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page
from wagtail.snippets.models import register_snippet
from wagtail.templatetags.wagtailcore_tags import richtext
from wagtailiconchooser.widgets import IconChooserWidget

from base.mixins import MetadataPageMixin
from base.models import AbstractBannerPage
from base.models import ServiceCategory
from base.utils import paginate, query_param_to_list, get_first_img_src, get_first_non_empty_p_string
from pages.news.blocks import ExternalLinkBlock

NEWS_ALLOWED_RICHTEXT_FEATURES = ['bold', 'italic', 'h4', 'h5', 'h6', 'ol', 'ul', 'hr', 'link', 'image',
                                  'document-link', 'embed', ]


@register_snippet
class NewsType(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    icon = models.CharField(max_length=100, null=True, blank=True)

    panels = [
        FieldPanel('name'),
        FieldPanel('icon', widget=IconChooserWidget),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("News Type")
        verbose_name_plural = _("News Types")


class NewsIndexPage(AbstractBannerPage):
    template = 'news_index_page.html'
    parent_page_types = ['home.HomePage']
    subpage_types = ['news.NewsPage']
    max_count = 1
    show_in_menus_default = True

    items_per_page = models.PositiveIntegerField(default=6, validators=[MinValueValidator(6), MaxValueValidator(20)],
                                                 verbose_name=_("Items per page"),
                                                 help_text=_("How many items should be visible on the news "
                                                             "landing page filter section ?"))
    content_panels = Page.content_panels + [
        *AbstractBannerPage.content_panels,
        MultiFieldPanel(
            [
                FieldPanel('items_per_page'),

            ],
            heading=_("Other settings"),
        )
    ]

    class Meta:
        verbose_name = _("News Index Page")

    @cached_property
    def filters(self):
        news_types = NewsType.objects.all()
        service_categories = ServiceCategory.objects.all()
        years = NewsPage.objects.dates("date", "year")

        return {
            "news_types": news_types,
            "service_categories": service_categories,
            "year": years
        }

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
        years = query_param_to_list(request.GET.get("year"), as_int=True)

        filters = models.Q()

        if news_types:
            filters &= models.Q(news_type__in=news_types)
        if services:
            filters &= models.Q(services__in=services)
        if years:
            filters &= models.Q(date__year__in=years)

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


class NewsPageTag(TaggedItemBase):
    content_object = ParentalKey('news.NewsPage', on_delete=models.CASCADE,
                                 related_name='news_tags')


class NewsPage(MetadataPageMixin, Page):
    template = 'news_detail_page.html'
    parent_page_types = ['news.NewsIndexPage']
    subpage_types = []

    news_type = models.ForeignKey(NewsType, on_delete=models.PROTECT, verbose_name=_("News type"))
    date = models.DateTimeField(_("Post date"), default=datetime.today)
    subtitle = models.TextField(blank=True, null=True, help_text=_("Optional subtitle"), verbose_name=_("Subtitle"))
    body = RichTextField(features=NEWS_ALLOWED_RICHTEXT_FEATURES, verbose_name=_("Body"))
    feature_img_src = models.TextField(blank=True, null=True, verbose_name=_("Feature Image"))
    services = ParentalManyToManyField('base.ServiceCategory', blank=True, verbose_name=_("Relevant Services"), )
    projects = ParentalManyToManyField('projects.ProjectPage', blank=True, verbose_name=_("Relevant Projects"))
    is_featured = models.BooleanField(default=False, help_text=_("Should this news appear on the news landing "
                                                                 "paging as the featured one ?"),
                                      verbose_name=_("Is featured"))
    is_alert = models.BooleanField(default=False, help_text=_("Is this an alert ?"), verbose_name=_("Is alert"))
    is_visible_on_homepage = models.BooleanField(default=False,
                                                 help_text=_("Should this appear in the homepage as"
                                                             " an alert/latest update ?"),
                                                 verbose_name=_("Is visible on homepage"))
    extra_links_heading = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Extra links heading"))

    external_links = StreamField([
        ('link', ExternalLinkBlock())
    ], blank=True, null=True, use_json_field=True, verbose_name=_("Extra links"))

    tags = ClusterTaggableManager(through=NewsPageTag, blank=True, verbose_name=_("Tags"))

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
        ], heading=_("Extra Links")),

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

    class Meta:
        verbose_name = _("News Page")

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
