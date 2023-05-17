from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import MultiFieldPanel,FieldPanel, StreamFieldPanel
# from wagtail.images.panels import ImageChooserPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import RichTextField, StreamField
from wagtail import blocks
from django.utils.functional import cached_property
from django.core.validators import MinValueValidator, MaxValueValidator
from wagtail_color_panel.edit_handlers import NativeColorPanel
from wagtail_color_panel.fields import ColorField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel, TabbedInterface, ObjectList
# Create your models here.


class Country(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    iso = models.CharField(max_length=100, verbose_name=_("ISO"))
    size = models.CharField(max_length=100, verbose_name=_("Size"))
    geom = models.MultiPolygonField(help_text=_("The paired values of points defining a polygon that delineates the affected "
                                         "area of the alert message"), null=True, srid=4326, verbose_name=_("Geometry"))


    def __str__(self):
        return self.name
    
@register_setting
class OrganisationSetting(BaseSiteSetting):
    # country 
    country = models.ForeignKey('Country', on_delete=models.CASCADE, related_name="country_setting", null=True, default="Ethiopia", verbose_name=_("Country"))
    
    # social media 
    twitter = models.URLField(max_length = 250, blank = True, null = True, help_text = _("Twitter url"), verbose_name=_("Twitter URL"))  
    facebook = models.URLField(max_length = 250, blank = True, null = True, help_text = _("Facebook url"), verbose_name=_("Facebook URL"))  
    youtube = models.URLField(max_length = 250, blank = True, null = True, help_text = _("Youtube url"), verbose_name=_("Youtube URL"))  
    instagram = models.URLField(max_length = 250, blank = True, null = True, help_text = _("Instagram url"), verbose_name=_("Instagram URL"))  
    phone = models.IntegerField(blank = True, null=True, help_text = _("Phone Number"), verbose_name=_("Phone number"))
    email = models.EmailField(blank = True, null=True, max_length=254, help_text = _("Email address"), verbose_name=_("Email address"))
    address = RichTextField(max_length = 250, blank=True,null=True, help_text = _("Postal Address"), verbose_name=_("Postal address"))

    # logo 
    logo = models.ForeignKey("wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+", verbose_name=_("Logo"))    

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("logo"),
            ],
            heading=_("Logo")
        ),
        MultiFieldPanel(
            [
                FieldPanel('country'),
            ],
            heading=_('Country')
        ),
        MultiFieldPanel([
            FieldPanel("address"),
        ], heading = _("Address Settings")),
        MultiFieldPanel([
            FieldPanel("email"),
            FieldPanel("phone"),
        ], heading = _("Contact Settings")),
        MultiFieldPanel([
            FieldPanel("twitter"),
            FieldPanel("facebook"),
            FieldPanel("youtube"),
            FieldPanel("instagram"),

        ], heading= _("Social Media Settings"))
    ]

    class Meta:
        verbose_name=_("Organisation Settings")


@register_setting(icon="cogs")
class IntegrationSettings(BaseSiteSetting):
    youtube_api = models.CharField(verbose_name=_("Youtube API Key"), max_length=50, blank=True,help_text=_("To set up Youtube API Key refer to https://developers.google.com/youtube/v3/getting-started"))
    mailchimp_api = models.CharField(verbose_name=_("Mailchimp API Key"), max_length=50,blank=True, help_text=_("To set up Mailchimp API Key refer to "))
    zoom_api_key = models.CharField(verbose_name=_("Zoom API Key"), blank=True,max_length=50, help_text=_("To set up Zoom API Key refer to "))
    zoom_api_secret = models.CharField(verbose_name=_("Zoom Secret Key"), blank=True,max_length=50, help_text=_("To set up Zoom Secret Key refer to "))

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
            'Track all button clicks using Google Analytics event tracking, ' 
            'Event tracking details can be specified in each button’s advanced settings options.'), )

    track_internally = models.BooleanField(
        default=False,
        verbose_name=_('Track pages internally'),
        help_text=_(
            'Track   all pages internally. This will enable the internal analytics dashboard, '
            'alongside Google Analytics, if also enabled'), )

    recaptcha_public_key =  models.CharField(
        blank=True,
        max_length=255,
        verbose_name=_('Recaptcha Public Key'),
        help_text=_('Your Recaptcha Public Key'),
    )

    recaptcha_private_key =  models.CharField(
        blank=True,
        max_length=255,
        verbose_name=_('Recaptcha Private Key'),
        help_text=_('Your Recaptcha Private Key'),
    )

    enable_auto_forecast =  models.BooleanField(
        default=True,
        verbose_name=_('Enable automated forecasts')
    )

    edit_handler = TabbedInterface([
        ObjectList([
            FieldPanel('enable_auto_forecast'),
        ],  heading=_("Forecasts Integration")),
        ObjectList([
            FieldPanel('recaptcha_public_key'),
            FieldPanel('recaptcha_private_key')
        ],  heading=_("Form Recaptcha Integration")),
        ObjectList([
            FieldPanel('youtube_api')
        ],  heading=_("Youtube Integration")),
        ObjectList([
            FieldPanel('mailchimp_api'),
        ],   heading=_("Mailchimp Integration")),
        ObjectList([
            FieldPanel('zoom_api_key'),
            FieldPanel('zoom_api_secret')
        ], heading=_("Zoom Integration")),
        ObjectList([
            FieldPanel('ga_tracking_id'),
            FieldPanel('ga_track_button_clicks'),
            FieldPanel('track_internally'),
        ], heading=_("Google Analytics")),
    ])

    class Meta:
        verbose_name=_("Integration Settings")
    
@register_setting(icon="site")
class LanguageSettings(BaseSiteSetting):
    languages = StreamField([
        ('languages', blocks.StructBlock([
            ('prefix', blocks.CharBlock(max_length=5)),
            ('language', blocks.CharBlock(max_length=20)),
            ('default', blocks.BooleanBlock(required=False)),
        ]))
    ], blank=True, null=True, use_json_field=False, verbose_name=_("languages"))

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
        help_text=_('A Unique key for managing submitted forms'),
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel('wagtail_form_key'),
            ],
            heading=_('Forms Security'),
        )
    ]

class Theme(models.Model):
    
    is_default = models.BooleanField(default=False, verbose_name=_("Is Default Theme"), help_text=_("Enable if this is the default theme"))
    name = models.CharField(blank=False, verbose_name=_("Theme Name"), max_length=250, null=True )
    primary_color = ColorField(blank=True, null=True, default="#363636", help_text=_("Primary color (use color picker)"))
    primary_hover_color = ColorField(blank=True, null=True, default="#176c9c", help_text=_("Primary Hover color (use color picker)"))
    secondary_color = ColorField(blank=True, null=True, default="#ffffff", help_text=_("Secondary color (use color picker)"))
    # secondary_hover_color = ColorField(blank=True, null=True, default="#ffffff", help_text=_("Secondary Hover color (use color picker)")
    border_radius = models.IntegerField(validators=[MinValueValidator(0),
                                       MaxValueValidator(20)],verbose_name=_("Border radius (px)"), help_text=_("Minimum 0 and Maximum 20 pixels"), default=6)
    box_shadow =  models.IntegerField(validators=[MinValueValidator(1),
                                       MaxValueValidator(24)],verbose_name=_("Box shadow"), help_text=_("Elevation value minimum 1 and maximum 24"), default=6)
    
    # bs_hr_off = models.IntegerField(validators=[MinValueValidator(-100),
    #                                    MaxValueValidator(100)],verbose_name=_("Horizontal Offset (px)", help_text=_("Minimum -100 and Maximum 100 pixels", default=0)
    
    # bs_vt_off = models.IntegerField(validators=[MinValueValidator(-100),
    #                                    MaxValueValidator(100)],verbose_name=_("Vertical Offset (px)", help_text=_("Minimum -100 and Maximum 100 pixels", default=1)
    
    # bs_blur_rad = models.IntegerField(validators=[MinValueValidator(-100),
    #                                    MaxValueValidator(100)],verbose_name=_("Blur radius (px)", help_text=_("Minimum -100 and Maximum 100 pixels", default=1)
    
    # bs_spread_rad = models.IntegerField(validators=[MinValueValidator(-100),
    #                                    MaxValueValidator(100)],verbose_name=_("Spread radius (px)", help_text=_("Minimum -100 and Maximum 100 pixels", default=-1)
    # bs_color = ColorField(blank=True, null=True, default="#363636", help_text=_("Box shadow color (use color picker)")
    # bs_color_opacity = models.DecimalField(validators=[MinValueValidator(0),
                                    #    MaxValueValidator(1)],decimal_places=3, max_digits=3, verbose_name=_("Color opacity", help_text=_("Minimum 0 and Maximum 1", default=0.125)
    
    edit_handler = TabbedInterface([
        ObjectList([
            FieldPanel('name'),
            FieldPanel('is_default'),
        ], heading=_("Information")),
        ObjectList([
            FieldRowPanel([
                NativeColorPanel('primary_color'),
                NativeColorPanel('primary_hover_color'),
            ]),
            FieldRowPanel([
                NativeColorPanel('secondary_color'),
            ])
        ], heading=_("Theme Colors")),
        ObjectList([
            FieldPanel('border_radius'), 
            FieldPanel('box_shadow')], 
            heading=_("Borders and Box Shadow")),
        # ObjectList([
        #     FieldRowPanel([
        #         FieldPanel('bs_hr_off'),
        #         FieldPanel('bs_vt_off'),
        #     ], heading=_("Offsets"),
        #     FieldRowPanel([
        #         FieldPanel('bs_blur_rad'),
        #         FieldPanel('bs_spread_rad'),
        #     ], heading=_("Radius"), 
        #     FieldRowPanel([
        #         NativeColorPanel('bs_color'),
        #         FieldPanel('bs_color_opacity'),
        #     ], heading=_("Color and Opacity"), 
            
        # ], heading=_("Box Shadow"),

    ])

    class Meta:
        verbose_name=_("Theme")

    def __str__(self) -> str:
        return self.name if not self.is_default else f"{self.name} (Default)"
    
    def save(self, *args, **kwargs):
        themes = Theme.objects.all().exclude(name=self.name)

        # when i default is enabled, disbale any other default theme 
        if self.is_default:
            themes.update(
                is_default=False
            )

        super(Theme, self).save(*args, **kwargs)
  

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
    temp_units = models.CharField(choices=TEMPERATURE_UNITS, default='celsius', max_length=255, verbose_name=_("Temperature"))  
    wind_units =  models.CharField(choices=WIND_UNITS, default='km_p_hr', max_length=255, verbose_name=_("Wind"))  

    panels = [
        FieldPanel("temp_units"),
        FieldPanel("wind_units"),
    ]

    class Meta:
        verbose_name=_("Measurement Settings")

