from adminboundarymanager.models import AdminBoundarySettings
from django.conf import settings
from django.contrib.gis.db import models
from django.template.defaultfilters import truncatechars
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from forecastmanager.forecast_settings import ForecastSetting
from geomanager.models import RasterFileLayer, WmsLayer, VectorTileLayer
from modelcluster.models import ClusterableModel
from wagtail import blocks
from wagtail.admin.panels import MultiFieldPanel, FieldPanel, TabbedInterface, ObjectList
from wagtail.api.v2.utils import get_full_url
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.contrib.settings.registry import register_setting
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail_color_panel.fields import ColorField
from wagtailiconchooser.blocks import IconChooserBlock
from wagtailiconchooser.utils import get_svg_sprite_for_icons
from wagtailmodelchooser import register_model_chooser

from climweb.base import blocks as climweb_blocks
from climweb.base.mixins import MetadataPageMixin
from climweb.base.registries import plugin_registry
from climweb.pages.events.models import EventPage
from climweb.pages.news.models import NewsPage
from climweb.pages.organisation_pages.partners.models import Partner
from climweb.pages.publications.models import PublicationPage
from climweb.pages.services.models import ServicePage
from climweb.pages.videos.models import YoutubePlaylist
from .blocks import AreaBoundaryBlock, AreaPolygonBlock

CLIMWEB_ADDITIONAL_APPS = getattr(settings, "CLIMWEB_ADDITIONAL_APPS", [])

HOME_SUBPAGE_TYPES = [
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

if "climweb.pages.aviation" in CLIMWEB_ADDITIONAL_APPS:
    HOME_SUBPAGE_TYPES.append('aviation.AviationPage')


class HomePage(MetadataPageMixin, Page):
    BANNER_TYPES = (
        ('full', 'Full Banner'),
        ('half', 'Half Banner'),
        ('card', 'Card Banner')
    )
    
    template = "home/home_page.html"
    
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
    
    call_to_action_button_text = models.CharField(max_length=100, blank=True, null=True,
                                                  verbose_name=_('Call to action button text'))
    call_to_action_related_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_('Call to action related page')
    )
    
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
        ('feature_item', climweb_blocks.FeatureBlock()),
    ], null=True, blank=True, use_json_field=True, verbose_name=_("Feature block"))
    
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("hero_banner"),
            FieldPanel('pre_title'),
            FieldPanel('hero_title'),
            FieldPanel('hero_subtitle'),
            FieldPanel('hero_type')
        ], heading=_("Banner Section")),
        MultiFieldPanel([
            FieldPanel('call_to_action_button_text'),
            FieldPanel('call_to_action_related_page'),
        ], heading=_("Banner Call to Action Button")),
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
    
    @classmethod
    @property
    def subpage_types(self):
        plugin_subpage_types = plugin_registry.get_plugin_subpage_types_for_page(self._meta.model_name)
        return HOME_SUBPAGE_TYPES + plugin_subpage_types
    
    def get_meta_image(self):
        if self.search_image:
            return self.search_image
        return self.hero_banner
    
    def save(self, *args, **kwargs):
        if not self.search_image and self.hero_banner:
            self.search_image = self.hero_banner
        
        if not self.seo_title and self.hero_title:
            self.seo_title = self.hero_title
        
        if not self.search_description and self.hero_subtitle:
            self.search_description = truncatechars(self.hero_subtitle, 160)
        
        return super().save(*args, **kwargs)
    
    def get_meta_description(self):
        if self.search_description:
            return self.search_description
        return self.hero_subtitle
    
    def get_meta_title(self):
        if self.seo_title:
            return self.seo_title
        return self.hero_title
    
    def get_context(self, request, *args, **kwargs):
        context = super(HomePage, self).get_context(request, *args, **kwargs)
        
        context["home_map_alerts_url"] = get_full_url(request, reverse("home_map_alerts"))
        
        abm_settings = AdminBoundarySettings.for_request(request)
        abm_extents = abm_settings.combined_countries_bounds
        context.update({
            "country_bounds": abm_extents,
        })
        
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
        
        home_map_settings = HomeMapSettings.for_request(request)
        home_map_layer_icons = [
            "warning",
            "heavy-rain",
            "layer-group"
        ]
        
        if home_map_settings.map_layers:
            icons = [layer_block.value.get("icon") for layer_block in home_map_settings.map_layers]
            home_map_layer_icons.extend(icons)
        
        context.update({
            "home_map_layer_svg_sprite": get_svg_sprite_for_icons(home_map_layer_icons)
        })
        
        return context
    
    @cached_property
    def partners(self):
        # get the first 6 partners that should be visible on the homepage
        partners = Partner.objects.filter(visible_on_homepage=True, logo__isnull=False)[:6]
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


register_model_chooser(WmsLayer)
register_model_chooser(VectorTileLayer)


class BaseLayerBlock(blocks.StructBlock):
    layer = blocks.CharBlock()  # placeholder for the actual layer chooser block, implemented in the subclasses
    icon = IconChooserBlock(required=False, default="layer-group", label=_("Icon"))
    display_name = blocks.CharBlock(max_length=100, required=False,
                                    help_text=_("Name to display on the map. "
                                                "Leave blank to use the original layer name"))
    default = blocks.BooleanBlock(default=False, required=False, label=_("Show on map by default ?"),
                                  help_text=_("You can only select one layer to be shown on the map by default. "
                                              "If multiple layers are selected, only the first one will be shown"))


class RasterFileLayerBlock(BaseLayerBlock):
    layer = climweb_blocks.UUIDModelChooserBlock(RasterFileLayer, icon="map")


class WMSLayerBlock(BaseLayerBlock):
    layer = climweb_blocks.UUIDModelChooserBlock(WmsLayer, icon="map")


class VectorTileLayerBlock(BaseLayerBlock):
    layer = climweb_blocks.UUIDModelChooserBlock(VectorTileLayer, icon="map")


@register_setting(icon="map")
class HomeMapSettings(BaseSiteSetting, ClusterableModel):
    DATE_FORMAT_CHOICES = (
        ("yyyy-MM-dd HH:mm", _("Hour minute:second - (E.g 2023-01-01 00:00)")),
        ("iii d HH:mm", _("Day of Week Day - (E.g Tue 25 08:00)")),
        ("yyyy-MM-dd", _("Day - (E.g 2023-01-01)")),
    )
    
    show_warnings_layer = models.BooleanField(default=True, verbose_name=_("Show CAP Warnings Layer"))
    warnings_layer_display_name = models.CharField(max_length=100, default=_("Weather Warnings"),
                                                   verbose_name=_("CAP Warnings Layer Display Name"))
    show_location_forecast_layer = models.BooleanField(default=True, verbose_name=_("Show Location forecast Layer"))
    location_forecast_layer_display_name = models.CharField(max_length=100, default=_("Location Forecast"),
                                                            verbose_name=_("Location Forecast Layer Display Name"))
    location_forecat_date_display_format = models.CharField(max_length=100, choices=DATE_FORMAT_CHOICES,
                                                            default="yyyy-MM-dd HH:mm",
                                                            help_text=_("Location Forecast Date Display Format"))
    forecast_cluster = models.BooleanField(default=False, verbose_name=_("Cluster Location Forecast Points"), )
    forecast_cluster_min_points = models.PositiveIntegerField(default=2, null=True, blank=True,
                                                              verbose_name=_("Cluster Minimum number of Points"),
                                                              help_text=_("Minimum number of points necessary to form"
                                                                          " a cluster if clustering is enabled"))
    forecast_cluster_radius = models.PositiveIntegerField(default=50, null=True, blank=True,
                                                          verbose_name=_("Cluster Radius"),
                                                          help_text=_("Radius of each cluster if clustering is "
                                                                      "enabled"))
    show_forecast_attribution = models.BooleanField(default=True, verbose_name=_("Show Location Forecast Attribution"))
    zoom_locations = StreamField([
        ("boundary_block", AreaBoundaryBlock(label=_("Admin Boundary"))),
        ("polygon_block", AreaPolygonBlock(label=_("Draw Polygon"))),
    ], use_json_field=True, blank=True)
    
    map_layers = StreamField([
        ('raster_file_layer', RasterFileLayerBlock(label=_("Raster Layer"), icon="map")),
        ('wms_layer', WMSLayerBlock(label=_("WMS Layer"), icon="map")),
        ('vector_tile_layer', VectorTileLayerBlock(label=_("Vector Tile Layer"), icon="map")),
    ], null=True, blank=True, max_num=5, verbose_name=_("Map Layers"))
    
    edit_handler = TabbedInterface([
        ObjectList([
            
            MultiFieldPanel([
                FieldPanel("show_warnings_layer"),
                FieldPanel("warnings_layer_display_name"),
            ], heading=_("CAP Warnings Layer"), ),
            
            MultiFieldPanel([
                FieldPanel("show_forecast_attribution"),
                FieldPanel("show_location_forecast_layer"),
                FieldPanel("location_forecast_layer_display_name"),
                FieldPanel("location_forecat_date_display_format"),
                FieldPanel("forecast_cluster"),
                FieldPanel("forecast_cluster_min_points"),
                FieldPanel("forecast_cluster_radius"),
            ], heading=_("Location Forecast Layer"), ),
            
            FieldPanel("zoom_locations"),
        ], heading=_("Map Settings")),
        ObjectList([
            FieldPanel("map_layers"),
        ], heading=_("Geomanager Map Layers")),
    ])
