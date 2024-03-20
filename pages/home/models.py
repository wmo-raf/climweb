import json

from adminboundarymanager.models import AdminBoundarySettings
from capeditor.constants import SEVERITY_MAPPING
from django.contrib.gis.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from forecastmanager.forecast_settings import ForecastSetting
from forecastmanager.models import City, CityForecast
from wagtail.admin.panels import MultiFieldPanel, FieldPanel
from wagtail.api.v2.utils import get_full_url
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.contrib.settings.registry import register_setting
from wagtail.fields import StreamField
from wagtail.models import Page, Site
from wagtail_color_panel.fields import ColorField

from base import blocks
from base.mixins import MetadataPageMixin
from pages.cap.models import CapAlertPage
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

    # don't cache home page
    cache_control = 'no-cache'

    hero_title = models.CharField(max_length=100, verbose_name=_('Title'))
    hero_subtitle = models.CharField(blank=True, null=True, max_length=100, verbose_name=_('Subtitle'))
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

    def get_context(self, request, *args, **kwargs):
        context = super(HomePage, self).get_context(
            request, *args, **kwargs)

        abm_settings = AdminBoundarySettings.for_request(request)
        abm_extents = abm_settings.combined_countries_bounds
        boundary_tiles_url = get_full_url(request, abm_settings.boundary_tiles_url)
        map_settings_url = get_full_url(request, reverse("home-map-settings"))

        context.update({
            "bounds": abm_extents,
            "boundary_tiles_url": boundary_tiles_url,
            "weather_icons_url": get_full_url(request, reverse("weather-icons")),
            "forecast_settings_url": get_full_url(request, reverse("forecast-settings")),
            "home_map_settings_url": map_settings_url
        })

        site = Site.objects.get(is_default_site=True)
        forecast_setting = ForecastSetting.for_site(site)

        city_detail_page = forecast_setting.weather_detail_page
        city_detail_page_url = None

        if city_detail_page:
            city_detail_page = city_detail_page.specific
            city_detail_page_url = city_detail_page.get_full_url(request)
            city_detail_page_url = city_detail_page_url + city_detail_page.detail_page_base_url
            context.update({
                "city_detail_page_url": city_detail_page_url,
            })

        city_search_url = get_full_url(request, reverse("cities-list"))
        context.update({
            "city_search_url": city_search_url,
            "city_detail_page_url": city_detail_page_url
        })

        default_city = forecast_setting.default_city
        if not default_city:
            default_city = City.objects.first()

        if default_city:
            default_city_forecasts = CityForecast.objects.filter(
                city=default_city,
                parent__forecast_date__gte=timezone.localtime(),
                parent__effective_period__default=True
            ).order_by("parent__forecast_date")

            # get unique forecast dates
            forecast_dates = default_city_forecasts.values_list("parent__forecast_date", flat=True).distinct()

            context.update({
                "default_city_forecasts": default_city_forecasts,
                "forecast_dates": forecast_dates,
            })

        if self.youtube_playlist:
            context['youtube_playlist_url'] = self.youtube_playlist.get_playlist_items_api_url(request)

        return context

    @cached_property
    def partners(self):
        # get partners that should appear on the homepage
        partners = Partner.objects.filter(visible_on_homepage=True)[:7]
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
    def cap_alerts(self):
        alerts = CapAlertPage.objects.all().live().filter(status="Actual")
        active_alert_infos = []
        geojson = {"type": "FeatureCollection", "features": []}

        for alert in alerts:
            for info in alert.info:
                if info.value.get('expires') > timezone.localtime():
                    start_time = info.value.get("effective") or alert.sent

                    if timezone.now() > start_time:
                        status = "Ongoing"
                    else:
                        status = "Expected"

                    area_desc = [area.get("areaDesc") for area in info.value.area]
                    area_desc = ",".join(area_desc)

                    alert_info = {
                        "status": status,
                        "url": alert.url,
                        "event": f"{info.value.get('event')} ({area_desc})",
                        "event_icon": info.value.event_icon,
                        "severity": SEVERITY_MAPPING[info.value.get("severity")]
                    }

                    active_alert_infos.append(alert_info)

                    if info.value.features:
                        for feature in info.value.features:
                            geojson["features"].append(feature)
        return {
            'active_alert_info': active_alert_infos,
            'geojson': json.dumps(geojson)
        }

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
