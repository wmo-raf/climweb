import os

from datetime import datetime, timedelta
from itertools import groupby

from django.contrib.gis.db import models
from django.utils.functional import cached_property
from django.core import serializers
import json

from wagtail.models import Page
from wagtail.admin.panels import MultiFieldPanel,FieldPanel
from wagtail_color_panel.fields import ColorField
from wagtail_color_panel.edit_handlers import NativeColorPanel
from wagtailgeowidget.helpers import geosgeometry_str_to_struct
from site_settings.models import Theme

from capeditor.models import Alert
from services.models import ServiceIndexPage
from forecast_manager.models import City, Forecast    
from layer_manager.models import WMSRequest, LegendItem, LayerCategory
from media_pages.videos.models import YoutubePlaylist
from media_pages.publications.models import PublicationPage
from media_pages.news.models import NewsPage
from organisation_pages.vacancies.models import VacancyDetailPage
from organisation_pages.events.models import EventPage

class HomePage(Page):
    template = "home_page.html"

    subpage_types = [
        'capeditor.AlertList', 
        'contact.ContactPage',
        'services.ServicesPage',
        'products.ProductIndexPage',
        'feedback.FeedbackPage',
        'publications.PublicationsIndexPage',
        'videos.VideoGalleryPage',
        'news.NewsIndexPage',
        'mediacenter.MediaIndexPage',
        'about.AboutIndexPage',
        'events.EventIndexPage'
    ]
    parent_page_type = [
        'wagtailcore.Page' 
    ]
    max_count = 1


    text_color = ColorField(blank=True, null=True, default="#f0f0f0")

    hero_title = models.CharField(blank=False, null=True, max_length=100, verbose_name='Title', default='National Meteorological & Hydrological Services')
    hero_subtitle = models.CharField(blank=False, null=True, max_length=100, verbose_name='Subtitle Title', default='Observing and understanding weather and climate')
    hero_banner = models.ForeignKey("wagtailimages.Image", 
        on_delete=models.SET_NULL, 
        null=True, blank=False, related_name="+")    

    enable_weather_forecasts = models.BooleanField(blank=True, default=True)
    enable_climate = models.BooleanField(blank=True, default=True)
    climate_title = models.CharField(blank=True, null=True, max_length=100, verbose_name='Climate Title', default='Explore Current Conditions')
    
    enable_media= models.BooleanField(blank=True, default=True)
    youtube_playlist = models.ForeignKey(
        YoutubePlaylist,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    video_section_title = models.CharField(blank=False, null=True, max_length=100, verbose_name='Media Section Title', default='Latest Media')
    video_section_desc = models.TextField(blank=False, null=True, max_length=500, verbose_name='Media Section Description', default='Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla accumsan, metus ultriceseleifend gt')

    content_panels = Page.content_panels+[
        MultiFieldPanel([
            NativeColorPanel('text_color'),
            FieldPanel('hero_title'),
            FieldPanel('hero_subtitle'),
            FieldPanel("hero_banner"),
        ], heading = "Hero Section"),
        MultiFieldPanel([
            FieldPanel('enable_weather_forecasts'),
            # FieldPanel('hero_subtitle')
        ], heading = "Weather forecasts Section"),
        MultiFieldPanel([
            FieldPanel('enable_climate'),
            FieldPanel('climate_title')
        ], heading = "Climate Section Section"),
        MultiFieldPanel([
            FieldPanel('enable_media'),
            FieldPanel('video_section_title'),
            FieldPanel('video_section_desc'),
            FieldPanel('youtube_playlist'),
        ], heading = "Media Section")

    ]

    class Meta:
        verbose_name = "Home Page"
        verbose_name_plural = "Home Pages"

    @cached_property
    def default_theme(self):
        theme = Theme.objects.get(is_default = True)
        # print("CURRENT THEME:", theme)

        context = {
            'primary_color': theme.primary_color,
            'secondary_color': theme.secondary_color,
            'border_radius': f"{theme.border_radius * 0.06}em",
        }

        return context
    

    @cached_property
    def city_item(self):
        cities = City.objects.all()
        return {'cities':cities.values()}

    @cached_property
    def get_forecast_by_city(request):

        start_date_param = datetime.today()
        end_date_param = start_date_param + timedelta(days=6)
        forecast_data = Forecast.objects.filter(forecast_date__gte=start_date_param.date(),  forecast_date__lte=end_date_param.date())\
                .order_by('forecast_date')\
                .values('id','city__name','forecast_date', 'max_temp', 'min_temp', 'wind_speed', 'wind_direction', 'condition__title','condition__icon_image', 'condition__icon_image__file')
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
            city_data = {'city':city, 'forecast_items': list(group)}

            for item in city_data['forecast_items']:
                # date_obj = datetime.strptime( item['forecast_date'], '%Y-%m-%d').date()
                item['forecast_date'] =item['forecast_date'].strftime('%a %d, %b').replace(' 0', ' ')

            grouped_forecast.append(city_data)
            

        return {
            'forecasts':grouped_forecast
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
    def get_forecast_by_daterange(request):
        start_date_param = datetime.today()
        end_date_param = start_date_param + timedelta(days=6)
        forecast_data = Forecast.objects.filter(forecast_date__gte=start_date_param.date(),  forecast_date__lte=end_date_param.date())\
                .values('id','city__name', 'city__location', 'forecast_date', 'max_temp', 'min_temp', 'wind_speed', 'wind_direction', 'condition__title', 'condition__icon_image', 'condition__icon_image__file')
        

        # sort the data by date
        data_sorted = sorted(forecast_data, key=lambda x: x['forecast_date'])

        # group the data by date
        grouped_forecast = []
        for forecast_date, group in groupby(data_sorted, lambda x: x['forecast_date']):
            city_data = {
                'forecast_date':forecast_date.strftime('%a %d, %b').replace(' 0', ' '), 
                'forecast_features': {}
            }


            forecast_features = []
            for forecast in list(group):
                location = geosgeometry_str_to_struct(str(forecast['city__location']))
                feature ={
                        "type": "Feature",
                        "properties": {
                            'id':forecast['id'],
                            'city_name':forecast['city__name'],
                            'forecast_date':forecast['forecast_date'].strftime('%a %d, %b').replace(' 0', ' '),
                            'max_temp':forecast['max_temp'],
                            'min_temp':forecast['min_temp'],
                            'wind_speed':forecast['wind_speed'],
                            'wind_direction':forecast['wind_direction'],
                            'media_path':f"{os.getenv('MEDIA_URL', '/media/')}",
                            'condition_icon':forecast['condition__icon_image__file'],
                            'condition_desc':forecast['condition__title'],
                        },
                        "geometry": {
                            "coordinates": [
                            location['x'],
                            location['y'],
                            ],
                            "type": "Point"
                    }
                }
            
                forecast_features.append(feature)

            city_data['forecast_features'] = {
                "type": "FeatureCollection",
                "features":forecast_features
            }

            grouped_forecast.append(city_data)
          

        return {
            'day_forecast':grouped_forecast
        }

    @cached_property
    def get_alerts(self):
        alerts = Alert.objects.all()
        active_alerts = alerts.filter(alert_info__expires__gte =datetime.today().date())[:3]
        return {
            # 'alerts': serializers.serialize('json',list(alerts) ),
            'alerts': alerts,
            'active_alerts':active_alerts
        }

    @cached_property
    def get_services(self):
        services = ServiceIndexPage.objects.live().public

        return {
            'services':services
        }

    @cached_property
    def get_cities(self):
        cities = City.objects.all()
        return {
            'cities':cities
        }

    @cached_property
    def get_wms_layers(self):
        wms_layers = WMSRequest.objects.all()
        wms_vals = list(wms_layers.values('id', 'title', 'subtitle', 'version', 'width', 'height','transparent', 'srs' , 'format', 'layers__name', 'legend_id', 'category_id', 'base_url', 'icon', 'icon__file'))
        for val in wms_vals:
            legends = LegendItem.objects.filter(legend_id =val['legend_id'] )
            category = LayerCategory.objects.get(id = val['category_id'])
            val['legend_colors'] = list(legends.values('item_val', 'item_color'))
            val['category'] = category.name
        
        
        return {
            'wms_layers':wms_vals,
            'wms_layers_json':json.dumps(wms_vals),
            'categories':list(LayerCategory.objects.all().values()),
            'categories_json':json.dumps(list(LayerCategory.objects.all().values()))
        }   

    

    # COMMON_PANELS = (
    #     FieldPanel('slug'),
    #     FieldPanel('seo_title'),
    #     FieldPanel('show_in_menus'),
    #     FieldPanel('search_description'),


    #     # add fields in any position you feel you have need for
    # )

    # promote_panels = [
    #     MultiFieldPanel(COMMON_PANELS, heading="Common page configuration"),
    # ]

