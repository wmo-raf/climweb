from wagtail.models import Page
from django.db import models
from wagtail.admin.edit_handlers import MultiFieldPanel,FieldPanel
from wagtail_color_panel.fields import ColorField
from wagtail_color_panel.edit_handlers import NativeColorPanel

    

class HomePage(Page):
    templates = "home_page.html"

    subpage_types = [
        'capeditor.AlertList',  # appname.ModelName
    ]
    parent_page_type = [
        'wagtailcore.Page'  # appname.ModelName
    ]

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


