from django.contrib.gis.db import models
from wagtail.admin.panels import MultiFieldPanel,FieldPanel, StreamFieldPanel
# from wagtail.images.panels import ImageChooserPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import RichTextField, StreamField
from wagtail import blocks
from django.utils.functional import cached_property

# Create your models here.


class Country(models.Model):
    name = models.CharField(max_length=100)
    iso = models.CharField(max_length=100)
    size = models.CharField(max_length=100)
    geom = models.MultiPolygonField(help_text="The paired values of points defining a polygon that delineates the affected "
                                         "area of the alert message", null=True, srid=4326)


    def __str__(self):
        return self.name
    
@register_setting
class OrganisationSetting(BaseSiteSetting):
    # country 
    country = models.ForeignKey('Country', on_delete=models.CASCADE, related_name="country_setting", null=True, default="Ethiopia")
    
    # social media 
    twitter = models.URLField(max_length = 250, blank = True, null = True, help_text = "Twitter url")  
    facebook = models.URLField(max_length = 250, blank = True, null = True, help_text = "Facebook url")  
    youtube = models.URLField(max_length = 250, blank = True, null = True, help_text = "Youtube url")  
    instagram = models.URLField(max_length = 250, blank = True, null = True, help_text = "Instagram url")  
    phone = models.IntegerField(blank = True, null=True, help_text = "Phone Number")
    email = models.EmailField(blank = True, null=True, max_length=254, help_text = "Email address")
    address = RichTextField(max_length = 250, blank=True,null=True, help_text = "Postal Address")

    # logo 
    logo = models.ForeignKey("wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")    

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("logo"),
            ],
            heading="Logo"
        ),
        MultiFieldPanel(
            [
                FieldPanel('country'),
            ],
            heading='Country'
        ),
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

@register_setting(icon='radio-full')
class MeasurementSettings(BaseSiteSetting):
    
    TEMPERATURE_UNITS = (
        ("celsius","°C"),
        ("fareinheit","°F"),
        ("kelvin", "K")
    )
    WIND_UNITS = (
        ("knots","knots"),
        ("km_p_hr","km/h"),
        ("mtr_p_s","m/s"),
        ("mile_p_hr", "mph"),
        ("feet_p_s", "ft/s")
    )
    temp_units = models.CharField(choices=TEMPERATURE_UNITS, default='celsius', max_length=255)  
    wind_units =  models.CharField(choices=WIND_UNITS, default='km_p_hr', max_length=255)  

    panels = [
        FieldPanel("temp_units"),
        FieldPanel("wind_units"),
    ]



@register_setting
class IntegrationSettings(BaseSiteSetting):
    youtube_api = models.CharField(verbose_name="Youtube API Key", max_length=50, blank=True,help_text="To set up Youtube API Key refer to https://developers.google.com/youtube/v3/getting-started")
    mailchimp_api = models.CharField(verbose_name="Mailchimp API Key", max_length=50,blank=True, help_text="To set up Mailchimp API Key refer to ")
    zoom_api_key = models.CharField(verbose_name="Zoom API Key", blank=True,max_length=50, help_text="To set up Zoom API Key refer to ")
    zoom_api_secret = models.CharField(verbose_name="Zoom Secret Key", blank=True,max_length=50, help_text="To set up Zoom Secret Key refer to ")

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

    recaptcha_public_key =  models.CharField(
        blank=True,
        max_length=255,
        verbose_name='Recaptcha Public Key',
        help_text='Your Recaptcha Public Key',
    )

    recaptcha_private_key =  models.CharField(
        blank=True,
        max_length=255,
        verbose_name='Recaptcha Private Key',
        help_text='Your Recaptcha Private Key',
    )

    panels = [
        MultiFieldPanel([
            FieldPanel('recaptcha_public_key'),
            FieldPanel('recaptcha_private_key')
        ], heading="Form Recaptcha Integration"),
        MultiFieldPanel([
            FieldPanel('youtube_api')
        ], heading="Youtube Integration"),
        MultiFieldPanel([
            FieldPanel('mailchimp_api')
        ], heading="Mailchimp Integration"),
        MultiFieldPanel([
            FieldPanel('zoom_api_key'),
            FieldPanel('zoom_api_secret')
        ], heading="Zoom Integration"),
        MultiFieldPanel(
            [
                FieldPanel('ga_tracking_id'),
                FieldPanel('ga_track_button_clicks'),
                FieldPanel('track_internally'),
            ],
            heading='Google Analytics'
        )
    ]
    
@register_setting(icon="site")
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
            heading='Forms Security',
        )
    ]
