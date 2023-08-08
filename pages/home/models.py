import json
from datetime import datetime, timedelta
from itertools import groupby

from django.contrib.gis.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from forecastmanager.models import City, Forecast
from wagtail.admin.panels import MultiFieldPanel, FieldPanel
from wagtail.models import Page
from wagtail_color_panel.edit_handlers import NativeColorPanel
from wagtail_color_panel.fields import ColorField

from base.mixins import MetadataPageMixin
from pages.cap.constants import SEVERITY_MAPPING
from pages.cap.models import CapAlertPage
from pages.events.models import EventPage
from pages.news.models import NewsPage
from pages.publications.models import PublicationPage
from pages.services.models import ServicePage
from pages.videos.models import YoutubePlaylist


class HomePage(MetadataPageMixin, Page):
    template = "home_page.html"

    subpage_types = [
        'cap.CapAlertPage',
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
        'cityclimate.CityClimateDataPage'
    ]
    parent_page_type = [
        'wagtailcore.Page'
    ]
    max_count = 1

    hero_title = models.CharField(max_length=100, verbose_name=_('Title'))
    hero_subtitle = models.CharField(blank=False, null=True, max_length=100, verbose_name=_('Subtitle'))
    hero_banner = models.ForeignKey("wagtailimages.Image", on_delete=models.SET_NULL, null=True, blank=False,
                                    related_name="+", verbose_name=_("Banner Image"))
    hero_text_color = ColorField(blank=True, null=True, default="#f0f0f0", verbose_name=_("Banner Text Color"))
    show_city_forecast = models.BooleanField(default=True, verbose_name=_("Show city forecast section"))

    show_weather_watch = models.BooleanField(default=True, verbose_name=_("Show weather watch section"))
    weather_watch_header = models.TextField(max_length=100, default="Our Weather Watch",
                                            verbose_name=_("Weather Watch Section header"))
    show_mapviewer_cta = models.BooleanField(default=False, verbose_name=_("Show MapViewer button"))
    mapviewer_cta_title = models.CharField(max_length=100, blank=True, null=True, default='Explore on MapViewer',
                                           verbose_name=_('MapViewer Call to Action Title'))
    mapviewer_cta_url = models.URLField(blank=True, null=True, verbose_name=_("Mapviewer URL"), )

    show_media_section = models.BooleanField(default=False, verbose_name=_("Show media section"))
    video_section_title = models.CharField(max_length=100, blank=True, null=True, default='Latest Media',
                                           verbose_name=_('Media Section Title'), )
    video_section_desc = models.TextField(max_length=500, blank=True, null=True,
                                          verbose_name=_('Media Section Description'))
    youtube_playlist = models.ForeignKey(
        YoutubePlaylist,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Youtube Playlist")
    )
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('hero_title'),
            FieldPanel('hero_subtitle'),
            FieldPanel("hero_banner"),
            NativeColorPanel('hero_text_color'),
        ], heading=_("Banner Section")),
        MultiFieldPanel([
            FieldPanel('show_city_forecast'),
        ], heading=_("City Forecast Section")),
        MultiFieldPanel([
            FieldPanel('show_weather_watch'),
            FieldPanel('show_mapviewer_cta'),
            FieldPanel('mapviewer_cta_title'),
            FieldPanel('mapviewer_cta_url')
        ], heading=_("Weather Watch Section")),
        MultiFieldPanel([
            FieldPanel('show_media_section'),
            FieldPanel('video_section_title'),
            FieldPanel('video_section_desc'),
            FieldPanel('youtube_playlist'),
        ], heading=_("Media Section"))

    ]

    class Meta:
        verbose_name = _("Home Page")
        verbose_name_plural = _("Home Pages")

    @cached_property
    def city_item(self):
        cities = City.objects.all()
        return {'cities': cities.values()}

    @cached_property
    def get_forecast_by_city(self):
        start_date_param = datetime.today()
        end_date_param = start_date_param + timedelta(days=6)
        forecast_data = Forecast.objects.filter(forecast_date__gte=start_date_param.date(),
                                                forecast_date__lte=end_date_param.date(),
                                                effective_period__whole_day=True) \
            .order_by('forecast_date') \
            .values('id', 'city__name', 'forecast_date', 'data_value',
                    'condition')
        # .annotate(
        #     forecast_date_str = Cast(
        #         TruncDate('forecast_date', DateField()), CharField(),
        #     ),
        # )

        # sort the data by city
        data_sorted = sorted(forecast_data, key=lambda x: x['city__name'])

        # group the data by city
        grouped_forecast = []
        for city, group in groupby(data_sorted, lambda x: x['city__name']):
            city_data = {'city': city, 'forecast_items': list(group)}

            for item in city_data['forecast_items']:
                # date_obj = datetime.strptime( item['forecast_date'], '%Y-%m-%d').date()
                item['forecast_date'] = item['forecast_date'].strftime('%a %d, %b').replace(' 0', ' ')
                item['condition_display'] = dict(Forecast.CONDITION_CHOICES).get(item['condition'])
            grouped_forecast.append(city_data)

        return {
            'forecasts': grouped_forecast
        }

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
    def get_forecast_by_daterange(self):
        start_date_param = datetime.today()
        end_date_param = start_date_param + timedelta(days=6)

        dates_ls = Forecast.objects.filter(forecast_date__gte=start_date_param.date(),
                                           forecast_date__lte=end_date_param.date()) \
            .order_by('forecast_date') \
            .values_list('forecast_date', flat=True) \
            .distinct()

        return {
            'forecast_dates': dates_ls
        }

    @cached_property
    def cap_alerts(self):
        alerts = CapAlertPage.objects.all().order_by('-sent')
        active_alert_infos = []
        geojson = {"type": "FeatureCollection", "features": []}

        for alert in alerts:
            for info in alert.info:
                if info.value.get('expires').date() >= datetime.today().date():
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

    @cached_property
    def get_cities(self):
        cities = City.objects.all()
        return {
            'cities': cities
        }
