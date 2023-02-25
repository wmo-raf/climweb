from django.db import models
from wagtail.admin.edit_handlers import MultiFieldPanel,FieldPanel
# from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.core.fields import RichTextField
from django.utils.translation import gettext_lazy as _

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
        verbose_name = _('Tracking')

    ga_tracking_id = models.CharField(
        blank=True,
        max_length=255,
        verbose_name=_('GA Tracking ID'),
        help_text=_('Your Google Analytics tracking ID (begins with "UA-")'),
    )
    ga_track_button_clicks = models.BooleanField(
        default=False,
        verbose_name=_('Track button clicks'),
        help_text=_(
            'Track all button clicks using Google Analytics event tracking. '
            'Event tracking details can be specified in each button’s advanced settings options.'),
    )

    track_internally = models.BooleanField(
        default=False,
        verbose_name=_('Track pages internally'),
        help_text=_(
            'Track all pages internally. This will enable the internal analytics dashboard, '
            'alongside Google Analytics, if also enabled'), )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel('ga_tracking_id'),
                FieldPanel('ga_track_button_clicks'),
                FieldPanel('track_internally'),
            ],
            heading=_('Google Analytics')
        )
    ]
