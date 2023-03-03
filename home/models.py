from datetime import datetime, timedelta
from itertools import groupby
import json

from django.contrib.gis.db import models
from django.utils.functional import cached_property
from django.http import JsonResponse
from django.db.models import Count

from wagtail.models import Page
from wagtail.admin.panels import MultiFieldPanel,FieldPanel
from wagtail_color_panel.fields import ColorField
from wagtail_color_panel.edit_handlers import NativeColorPanel

from capeditor.models import Alert
from services.models import ServiceIndexPage
from forecast_manager.models import City, Forecast, ConditionCategory     

class HomePage(Page):
    templates = "home_page.html"

    subpage_types = [
        'capeditor.AlertList', 
        'contact.ContactPage',
        'services.ServicesPage',
        'products.ProductsPage',
        'feedback.FeedbackPage',
        'vacancies.VacanciesPage',
        'publications.PublicationsIndexPage',
        'videos.VideoGalleryPage',
        'news.NewsIndexPage',
        'projects.ProjectIndexPage',
        'mediacenter.MediaIndexPage',
        'tenders.TendersPage',
        'about.AboutPage',
        'about.PartnersPage',
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
        ], heading = "Climate Section Section")
    ]
    

    class Meta:
        verbose_name = "Home Page"
        verbose_name_plural = "Home Pages"

    @cached_property
    def city_item(self):
        cities = City.objects.all()
        return {'cities':cities.values()}

    @cached_property
    def get_forecast_by_city(request):

        start_date_param = datetime.today()
        end_date_param = start_date_param + timedelta(days=7)
        forecast_data = Forecast.objects.filter(forecast_date__gte=start_date_param.date(),  forecast_date__lte=end_date_param.date()).order_by('forecast_date').values('id','city','forecast_date', 'max_temp', 'min_temp', 'wind_speed', 'wind_direction', 'condition').annotate()

        # sort the data by city
        data_sorted = sorted(forecast_data, key=lambda x: x['city'])

        # group the data by city
        grouped_forecast = []
        for city, group in groupby(data_sorted, lambda x: x['city']):
            city_data = {'city':City.objects.get(id=city), 'forecast_items': list(group)}

            for item in city_data['forecast_items']:
                item['condition'] = ConditionCategory.objects.get(id=item['condition'])

            grouped_forecast.append(city_data)

        return {
            'forecasts':grouped_forecast
        }

    @cached_property
    def get_alerts(self):
        alerts = Alert.objects.live().public()
        latest_alerts = alerts[:3]

        return {
            'alerts': alerts,
            'latest_alerts':latest_alerts
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

