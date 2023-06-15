from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.gis.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.admin.panels import (
    PageChooserPanel,
    MultiFieldPanel,
    FieldPanel,
    TabbedInterface,
    ObjectList,
    FieldRowPanel
)
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.contrib.settings.registry import register_setting
from wagtail.fields import RichTextField, StreamField
from wagtail_color_panel.edit_handlers import NativeColorPanel
from wagtail_color_panel.fields import ColorField

from base.blocks import NavigationItemBlock, FooterNavigationItemBlock


class Country(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    iso = models.CharField(max_length=100, verbose_name=_("ISO"))
    size = models.CharField(max_length=100, verbose_name=_("Size"))
    geom = models.MultiPolygonField(
        help_text=_("The paired values of points defining a polygon that delineates the affected "
                    "area of the alert message"), null=True, srid=4326, verbose_name=_("Geometry"))

    def __str__(self):
        return self.name


@register_setting
class OrganisationSetting(BaseSiteSetting):
<<<<<<< HEAD:site_settings/models.py
    # country 
    country = models.ForeignKey('Country', on_delete=models.CASCADE, related_name="country_setting", null=True, verbose_name=_("Country"))

    # social media 
=======
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Organisation Name"))
    # country
    country = models.ForeignKey('Country', blank=True, null=True, on_delete=models.CASCADE,
                                related_name="country_setting",
                                verbose_name=_("Country"))
    # social media
>>>>>>> fa5553882b7688c84810350fe450698bb1b8a35f:base/models/site_settings.py
    twitter = models.URLField(max_length=250, blank=True, null=True, help_text=_("Twitter url"),
                              verbose_name=_("Twitter URL"))
    facebook = models.URLField(max_length=250, blank=True, null=True, help_text=_("Facebook url"),
                               verbose_name=_("Facebook URL"))
    youtube = models.URLField(max_length=250, blank=True, null=True, help_text=_("Youtube url"),
                              verbose_name=_("Youtube URL"))
    instagram = models.URLField(max_length=250, blank=True, null=True, help_text=_("Instagram url"),
                                verbose_name=_("Instagram URL"))
    phone = models.IntegerField(blank=True, null=True, help_text=_("Phone Number"), verbose_name=_("Phone number"))
    email = models.EmailField(blank=True, null=True, max_length=254, help_text=_("Email address"),
                              verbose_name=_("Email address"))
    address = RichTextField(max_length=250, blank=True, null=True, help_text=_("Postal Address"),
                            verbose_name=_("Postal address"))

    # logo
    logo = models.ForeignKey("wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
                             verbose_name=_("Logo"))

    favicon = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Does not need to be any larger than 200x200 pixels. A 1:1 (square) image ratio is best here "
                  "- If the image is not square, it will be scaled to a square."
    )

    footer_logo = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Footer Logo"),
        help_text=_("Logo that appears on the footer"),
    )

    cms_logo = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("CMS Logo"),
        help_text=_("Logo that appears on the CMS. Should be a whit transparent logo preferably"),
    )

    page_not_found_error_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Page not Found Image"),
        help_text=_("Image shown on error 404 page"),
    )

    server_error_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Server Error Image"),
        help_text=_("Image shown on error 500 error page"),
    )

    panels = [
        FieldPanel("name"),
        MultiFieldPanel(
            [
                FieldPanel("logo"),
                FieldPanel("favicon"),
                FieldPanel("footer_logo"),
                FieldPanel("cms_logo"),
            ],
            heading=_("Logo")
        ),
        MultiFieldPanel(
            [
                FieldPanel("page_not_found_error_image"),
                FieldPanel("server_error_image"),
            ],
            heading=_("Error Images")
        ),
        MultiFieldPanel(
            [
                FieldPanel('country'),
            ],
            heading=_('Country')
        ),
        MultiFieldPanel([
            FieldPanel("address"),
        ], heading=_("Address Settings")),
        MultiFieldPanel([
            FieldPanel("email"),
            FieldPanel("phone"),
        ], heading=_("Contact Settings")),
        MultiFieldPanel([
            FieldPanel("twitter"),
            FieldPanel("facebook"),
            FieldPanel("youtube"),
            FieldPanel("instagram"),

        ], heading=_("Social Media Settings"))
    ]

    class Meta:
        verbose_name = _("Organisation Settings")


@register_setting(icon="cogs")
class IntegrationSettings(BaseSiteSetting):
    youtube_api = models.CharField(verbose_name=_("Youtube API Key"), max_length=50, blank=True, help_text=_(
        "To set up Youtube API Key refer to https://developers.google.com/youtube/v3/getting-started"))

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

    recaptcha_public_key = models.CharField(
        blank=True,
        max_length=255,
        verbose_name=_('Recaptcha Public Key'),
        help_text=_('Your Recaptcha Public Key'),
    )

    recaptcha_private_key = models.CharField(
        blank=True,
        max_length=255,
        verbose_name=_('Recaptcha Private Key'),
        help_text=_('Your Recaptcha Private Key'),
    )

    enable_auto_forecast = models.BooleanField(
        default=True,
        verbose_name=_('Enable automated forecasts')
    )

    edit_handler = TabbedInterface([
        ObjectList([
            FieldPanel('enable_auto_forecast'),
        ], heading=_("Forecasts Integration")),
        ObjectList([
            FieldPanel('recaptcha_public_key'),
            FieldPanel('recaptcha_private_key')
        ], heading=_("Form Recaptcha Integration")),
        ObjectList([
            FieldPanel('youtube_api')
        ], heading=_("Youtube Integration")),
        ObjectList([
            FieldPanel('ga_tracking_id'),
            FieldPanel('ga_track_button_clicks'),
            FieldPanel('track_internally'),
        ], heading=_("Google Analytics")),
    ])

    class Meta:
        verbose_name = _("Integration Settings")


@register_setting(icon="site")
class LanguageSettings(BaseSiteSetting):
    languages = StreamField([
        ('languages', blocks.StructBlock([
            ('prefix', blocks.CharBlock(max_length=5)),
            ('language', blocks.CharBlock(max_length=20)),
            ('default', blocks.BooleanBlock(required=False)),
        ]))
    ], blank=True, null=True, use_json_field=True, verbose_name=_("languages"))

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
    is_default = models.BooleanField(default=False, verbose_name=_("Is Default Theme"),
                                     help_text=_("Enable if this is the default theme"))
    name = models.CharField(blank=False, verbose_name=_("Theme Name"), max_length=250, null=True)
    primary_color = ColorField(blank=True, null=True, default="#363636",
                               help_text=_("Primary color (use color picker)"))
    primary_hover_color = ColorField(blank=True, null=True, default="#176c9c",
                                     help_text=_("Primary Hover color (use color picker)"))
    secondary_color = ColorField(blank=True, null=True, default="#ffffff",
                                 help_text=_("Secondary color (use color picker)"))
    # secondary_hover_color = ColorField(blank=True, null=True, default="#ffffff", help_text=_("Secondary Hover color (use color picker)")
    border_radius = models.IntegerField(validators=[MinValueValidator(0),
                                                    MaxValueValidator(20)], verbose_name=_("Border radius (px)"),
                                        help_text=_("Minimum 0 and Maximum 20 pixels"), default=6)
    box_shadow = models.IntegerField(validators=[MinValueValidator(1),
                                                 MaxValueValidator(24)], verbose_name=_("Box shadow"),
                                     help_text=_("Elevation value minimum 1 and maximum 24"), default=6)

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
        verbose_name = _("Theme")

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
        ("celsius", "°C"),
        ("fareinheit", "°F"),
        ("kelvin", "K")
    )
    WIND_UNITS = (
        ("knots", "knots"),
        ("km_p_hr", "km/h"),
        ("mtr_p_s", "m/s"),
        ("mile_p_hr", "mph"),
        ("feet_p_s", "ft/s")
    )
    temp_units = models.CharField(choices=TEMPERATURE_UNITS, default='celsius', max_length=255,
                                  verbose_name=_("Temperature"))
    wind_units = models.CharField(choices=WIND_UNITS, default='km_p_hr', max_length=255, verbose_name=_("Wind"))

    panels = [
        FieldPanel("temp_units"),
        FieldPanel("wind_units"),
    ]

    class Meta:
        verbose_name = _("Measurement Settings")


@register_setting
class NavigationSettings(BaseSiteSetting):
    main_menu = StreamField([
        ("navigation_item", NavigationItemBlock()),
    ], use_json_field=True, blank=True, null=True)
    footer_menu = StreamField([
        ("navigation_item", FooterNavigationItemBlock()),
    ], use_json_field=True, blank=True, null=True)

    panels = [
        FieldPanel("main_menu"),
        FieldPanel("footer_menu"),
    ]


@register_setting
class ImportantPages(BaseSiteSetting):
    mailing_list_signup_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("Mailing list sign up page"))
    contact_us_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("Contact us page"))
    all_products_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("All products page"))
    all_projects_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("All projects page"))
    all_alerts_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("All alerts page"))
    all_news_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("All news page"))
    all_publications_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("All publications page"))
    all_videos_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("All videos page"))
    all_applications_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("All applications page"))
    all_events_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("All events page"))
    all_partners_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("All partners page"))
    all_tenders_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("All tenders page"))
    all_vacancies_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("All vacancies page"))
    feedback_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("Feedback page"))

    panels = [
        PageChooserPanel('mailing_list_signup_page'),
        PageChooserPanel('contact_us_page'),
        PageChooserPanel('feedback_page'),
        PageChooserPanel('all_products_page'),
        PageChooserPanel('all_projects_page'),
        PageChooserPanel('all_tenders_page'),
        PageChooserPanel('all_vacancies_page'),
        PageChooserPanel('all_alerts_page'),
        PageChooserPanel('all_news_page'),
        PageChooserPanel('all_publications_page'),
        PageChooserPanel('all_videos_page'),
        PageChooserPanel('all_applications_page'),
        PageChooserPanel('all_events_page'),
        PageChooserPanel('all_partners_page'),
    ]
