from django.contrib.gis.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from forecastmanager.forecast_settings import ForecastSetting
from wagtail.admin.panels import MultiFieldPanel, FieldPanel
from wagtail.api.v2.utils import get_full_url
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.contrib.settings.registry import register_setting
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail_color_panel.fields import ColorField
from django.template.defaultfilters import truncatechars
from base.utils import get_first_non_empty_p_string

from base import blocks
from base.mixins import MetadataPageMixin
from pages.events.models import EventPage
from pages.home.blocks import AreaBoundaryBlock, AreaPolygonBlock
from pages.news.models import NewsPage
from pages.organisation_pages.partners.models import Partner
from pages.publications.models import PublicationPage
from pages.services.models import ServicePage
from pages.videos.models import YoutubePlaylist


class HomePage(MetadataPageMixin, Page):
    BANNER_TYPES = (
        ('full', 'Full Banner'),
        ('half', 'Half Banner'),
        ('card', 'Card Banner')
    )

    template = "home/home_page.html"

    subpage_types = [
        'weather.WeatherDetailPage',
        'contact.ContactPage',
        'services.ServiceIndexPage',
        'products.ProductIndexPage',
        'feedback.FeedbackPage',
        'publications.PublicationsIndexPage',
        'news.NewsIndexPage',
        'mediacenter.MediaIndexPage',
        'organisation.OrganisationIndexPage',
        'events.EventIndexPage',
        'surveys.SurveyPage',
        'email_subscription.MailchimpMailingListSubscriptionPage',
        'email_subscription.MauticMailingListSubscriptionPage',
        'data_request.DataRequestPage',
        'flex_page.FlexPage',
        'stations.StationsPage',
        'satellite_imagery.SatelliteImageryPage',
        'cityclimate.CityClimateDataPage',
        'cap.CapAlertListPage',
        'glossary.GlossaryIndexPage',
        'webstories.WebStoryListPage',
        
    ]
    parent_page_type = [
        'wagtailcore.Page'
    ]
    max_count = 1

    pre_title = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Pre Title'),
                                 help_text=_("Text to show before the name of the institution. "
                                             "For example, if the institution is under a ministry, the ministry name "
                                             "can added here"))
    hero_title = models.CharField(max_length=100, verbose_name=_('Institution Name'),
                                  help_text=_("Full name of the institution"))
    hero_subtitle = models.CharField(blank=True, null=True, max_length=100, verbose_name=_('Tagline'),
                                     help_text=_("Can be the tagline or slogan of the institution"))
    hero_banner = models.ForeignKey("wagtailimages.Image", on_delete=models.SET_NULL, null=True, blank=False,
                                    related_name="+", verbose_name=_("Banner Image"))
    hero_text_color = ColorField(blank=True, null=True, default="#f0f0f0", verbose_name=_("Banner Text Color"))
    hero_type = models.CharField(_("Banner Type"), max_length=50, choices=BANNER_TYPES, default='full')

    show_city_forecast = models.BooleanField(default=True, verbose_name=_("Show city forecast section"))

    show_weather_watch = models.BooleanField(default=True, verbose_name=_("Show weather watch section"))
    weather_watch_header = models.CharField(max_length=100, default="Our Weather Watch",
                                            verbose_name=_("Weather Watch Section header"))
    show_mapviewer_cta = models.BooleanField(default=False, verbose_name=_("Show MapViewer button"))
    mapviewer_cta_title = models.CharField(max_length=100, blank=True, null=True, default='Explore on MapViewer',
                                           verbose_name=_('MapViewer Call to Action Title'))
    mapviewer_cta_url = models.URLField(blank=True, null=True, verbose_name=_("Mapviewer URL"), )

    youtube_playlist = models.ForeignKey(
        YoutubePlaylist,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Youtube Playlist")
    )

    feature_block = StreamField([
        ('feature_item', blocks.FeatureBlock()),
    ], null=True, blank=True, use_json_field=True, verbose_name=_("Feature block"))

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('pre_title'),
            FieldPanel('hero_title'),
            FieldPanel('hero_subtitle'),
            FieldPanel("hero_banner"),
            # NativeColorPanel('hero_text_color'),
            FieldPanel('hero_type')
        ], heading=_("Banner Section")),
        MultiFieldPanel([
            FieldPanel('show_city_forecast'),
        ], heading=_("City Forecast Section")),
        MultiFieldPanel([
            FieldPanel('show_weather_watch'),
            FieldPanel('weather_watch_header'),
            FieldPanel('show_mapviewer_cta'),
            FieldPanel('mapviewer_cta_title'),
            FieldPanel('mapviewer_cta_url')
        ], heading=_("Weather Watch Section")),
        MultiFieldPanel([
            FieldPanel('youtube_playlist'),
        ], heading=_("Media Section")),
        MultiFieldPanel([
            FieldPanel('feature_block'),

        ], heading=_("Addditional Information")),

    ]

    class Meta:
        verbose_name = _("Home Page")
        verbose_name_plural = _("Home Pages")

    def get_meta_image(self):
        if self.search_image:
            return self.search_image
        return self.hero_banner
    
    def save(self, *args, **kwargs):
        if not self.search_image and self.hero_banner:
            self.search_image = self.hero_banner
            
        if not self.seo_title and  self.hero_title:
            self.seo_title = self.hero_title
            print("SEO_TITLE", self.seo_title)

        if not self.search_description and self.hero_subtitle:
            self.search_description = truncatechars(self.hero_subtitle, 160)
            print("SEO_subtitle", self.search_description)

        return super().save(*args, **kwargs)

    def get_meta_description(self):
        if self.search_description:
            return self.search_description
        return self.hero_subtitle

    def get_context(self, request, *args, **kwargs):
        context = super(HomePage, self).get_context(request, *args, **kwargs)

        forecast_setting = ForecastSetting.for_request(request)
        city_detail_page = forecast_setting.weather_detail_page

        if city_detail_page:
            city_detail_page = city_detail_page.specific
            all_city_detail_page_url = city_detail_page.get_full_url(request)
            city_detail_page_url = all_city_detail_page_url + city_detail_page.detail_page_base_url
            context.update({
                "city_detail_page_url": city_detail_page_url,
            })

        city_search_url = get_full_url(request, reverse("cities-list"))
        context.update({
            "city_search_url": city_search_url,
        })

        map_settings_url = get_full_url(request, reverse("home-map-settings"))
        context.update({
            "home_map_settings_url": map_settings_url,
            "home_weather_widget_url": get_full_url(request, reverse("home-weather-widget")),
        })

        if self.youtube_playlist:
            context['youtube_playlist_url'] = self.youtube_playlist.get_playlist_items_api_url(request)

        return context

    @cached_property
    def partners(self):
        # get the first 6 partners that should be visible on the homepage
        partners = Partner.objects.filter(visible_on_homepage=True)[:6]
        return partners

    @cached_property
    def latest_updates(self):
        updates = []

        # get latest news, publication, crop monitor, seasonal forecast, food security statement,
        news = NewsPage.objects.live().filter(is_visible_on_homepage=True).order_by('-date').first()
        events = EventPage.objects.live().filter(is_visible_on_homepage=True).order_by('-date_from').first()

        if events is None:
            events = EventPage.objects.live().order_by('-date_from').first()

        if news is None:
            news = NewsPage.objects.live().order_by('-date').first()

        publications = PublicationPage.objects.live().filter(is_visible_on_homepage=True).order_by(
            '-publication_date').first()

        if publications is None:
            publications = PublicationPage.objects.live().order_by('-publication_date').first()

        if news:
            updates.append(news)
        if events:
            updates.append(events)
        if publications:
            updates.append(publications)

        return updates

    @cached_property
    def services(self):
        services = ServicePage.objects.live()
        return services


@register_setting(icon="map")
class HomeMapSettings(BaseSiteSetting):
    zoom_locations = StreamField([
        ("boundary_block", AreaBoundaryBlock(label=_("Admin Boundary"))),
        ("polygon_block", AreaPolygonBlock(label=_("Draw Polygon"))),
    ], use_json_field=True, blank=True)
