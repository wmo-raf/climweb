from django.contrib.gis.db import models
from wagtail.admin.panels import MultiFieldPanel,FieldPanel, StreamFieldPanel
# from wagtail.images.panels import ImageChooserPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import RichTextField, StreamField
from wagtail import blocks
from django.utils.functional import cached_property

# Create your models here.
@register_setting(icon='radio-full')
class MeasurementSettings(BaseSiteSetting):
    
    TEMPERATURE_UNITS = (
        ("celsius","°C"),
        ("fareinheit","°F")
    )
    WIND_UNITS = (
        ("knots","knots"),
        ("km_p_hr","km/h"),
        ("m_p_s","m/s")
    )
    temp_units = models.CharField(choices=TEMPERATURE_UNITS, default='celsius', max_length=255)  
    wind_units =  models.CharField(choices=WIND_UNITS, default='km_p_hr', max_length=255)  

    panels = [
        FieldPanel("temp_units"),
        FieldPanel("wind_units"),
    ]
    


@register_setting
class LogoAndMottoSettings(BaseSiteSetting):
    motto = models.CharField(blank=True,null=True, max_length=50)
    logo = models.ForeignKey("wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")    

    panels = [
        FieldPanel("motto"),
        FieldPanel("logo"),
    ]

@register_setting
class SocialAndAddressSettings(BaseSiteSetting):
    twitter = models.URLField(max_length = 250, blank = True, null = True, help_text = "Twitter handle")  
    facebook = models.URLField(max_length = 250, blank = True, null = True, help_text = "Facebook handle")  
    youtube = models.URLField(max_length = 250, blank = True, null = True, help_text = "Youtube handle")  
    instagram = models.URLField(max_length = 250, blank = True, null = True, help_text = "Instagram handle")  
    phone = models.IntegerField(blank = True, null=True, help_text = "Phone Number")
    email = models.EmailField(blank = True, null=True, max_length=254, help_text = "Email address")
    address = RichTextField(max_length = 250, blank=True,null=True, help_text = "Postal Address")

    panels = [
         MultiFieldPanel([
            FieldPanel("address"),
        ], heading = "Address Settings"),
        MultiFieldPanel([
            FieldPanel("email"),
            FieldPanel("phone"),
        ], heading = "Contact Settings"),
        MultiFieldPanel([
            FieldPanel("twitter"),
            FieldPanel("facebook"),
            FieldPanel("youtube"),
            FieldPanel("instagram"),

        ], heading= "Social Media Settings")
    ]

@register_setting()
class AnalyticsSettings(BaseSiteSetting):
    """
    Tracking and Google Analytics.
    """

    class Meta:
        verbose_name = ('Tracking')

    ga_tracking_id = models.CharField(
        blank=True,
        max_length=255,
        verbose_name='GA Tracking ID',
        help_text='Your Google Analytics tracking ID (begins with "UA-")',
    )
    ga_track_button_clicks = models.BooleanField(
        default=False,
        verbose_name=('Track button clicks'),
        help_text=(
            'Track all button clicks using Google Analytics event tracking, ' 
            'Event tracking details can be specified in each button’s advanced settings options.'), )

    track_internally = models.BooleanField(
        default=False,
        verbose_name=('Track pages internally'),
        help_text=(
            'Track   all pages internally. This will enable the internal analytics dashboard, '
            'alongside Google Analytics, if also enabled'), )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel('ga_tracking_id'),
                FieldPanel('ga_track_button_clicks'),
                FieldPanel('track_internally'),
            ],
            heading='Google Analytics'
        )
    ]

class Country(models.Model):
    name = models.CharField(max_length=100)
    iso = models.CharField(max_length=100)
    size = models.CharField(max_length=100)
    geom = models.MultiPolygonField(help_text="The paired values of points defining a polygon that delineates the affected "
                                         "area of the alert message", null=True, srid=4326)


    def __str__(self):
        return self.name
    
@register_setting
class CountrySetting(BaseSiteSetting):
    country = models.ForeignKey('Country', on_delete=models.CASCADE, related_name="country_setting", null=True)
    
    panels = [
        MultiFieldPanel(
            [
                FieldPanel('country'),
            ],
            heading='Country'
        )
    ]

@register_setting(icon="fa-language")
class LanguageSettings(BaseSiteSetting):
    languages = StreamField([
        ('languages', blocks.StructBlock([
            ('prefix', blocks.CharBlock(max_length=5)),
            ('language', blocks.CharBlock(max_length=20)),
            ('default', blocks.BooleanBlock(required=False)),
        ]))
    ], blank=True, null=True, use_json_field=False)

    panels = [
            FieldPanel('languages')
    ]

    class Meta:
        verbose_name = "Languages"

    @cached_property
    def get_list(self):
        return list(map(lambda x: x.value['prefix'], self.languages))


@register_setting()
class OtherSettings(BaseSiteSetting):
    wagtail_form_key = models.CharField(
        blank=True,
        max_length=255,
        help_text=('A Unique key for managing submitted forms'),
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel('wagtail_form_key'),
            ],
            heading='Forms Security'
        )
    ]