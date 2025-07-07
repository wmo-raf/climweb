from django.contrib.gis.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from loguru import logger
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
from wagtailcache.cache import clear_cache

from climweb.base.blocks import NavigationItemBlock, FooterNavigationItemBlock, LanguageItemBlock, SocialMediaBlock
from climweb.base.constants import LANGUAGE_CHOICES, LANGUAGE_CHOICES_DICT, COUNTRY_CHOICES
from climweb.base.utils import get_country_info
from django.conf import settings


@register_setting
class OrganisationSetting(BaseSiteSetting):
    country = models.CharField(max_length=100, blank=True, null=True, choices=COUNTRY_CHOICES,
                               verbose_name=_("Country"))
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Organisation Name"))
    
    phone = models.CharField(max_length=255, blank=True, null=True, help_text=_("Phone Number"),
                             verbose_name=_("Phone number"))
    email = models.EmailField(blank=True, null=True, max_length=254, help_text=_("Email address"),
                              verbose_name=_("Email address"))
    address = RichTextField(max_length=250, blank=True, null=True, help_text=_("Postal Address"),
                            verbose_name=_("Postal address"))
    
    social_media_accounts = StreamField([
        ('social_media_account', SocialMediaBlock()),
    ], blank=True, null=True, use_json_field=True)
    
    # logo
    logo = models.ForeignKey("wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
                             verbose_name=_("Organisation Logo"))
    country_flag = models.ForeignKey("wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL,
                                     related_name="+",
                                     verbose_name=_("Country Flag"))
    
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
        FieldPanel('country'),
        MultiFieldPanel(
            [
                FieldPanel("logo"),
                FieldPanel("country_flag"),
                FieldPanel("favicon"),
                FieldPanel("footer_logo"),
                FieldPanel("cms_logo"),
            ],
            heading=_("Logo")
        ),
        FieldPanel("social_media_accounts"),
        MultiFieldPanel(
            [
                FieldPanel("page_not_found_error_image"),
                FieldPanel("server_error_image"),
            ],
            heading=_("Error Images")
        ),
        
        MultiFieldPanel([
            FieldPanel("address"),
        ], heading=_("Address Settings")),
        MultiFieldPanel([
            FieldPanel("email"),
            FieldPanel("phone"),
        ], heading=_("Contact Settings")),
    ]
    
    class Meta:
        verbose_name = _("Organisation Settings")
    
    @cached_property
    def country_info(self):
        if self.country:
            return get_country_info(self.country)


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
    
    google_site_verification_key = models.CharField(max_length=255, blank=True, null=True,
                                                    verbose_name=_("Google Site Verification Key"), )
    
    edit_handler = TabbedInterface([
        ObjectList([
            FieldPanel('youtube_api')
        ], heading=_("Youtube Integration")),
        ObjectList([
            FieldPanel('ga_tracking_id'),
            FieldPanel('ga_track_button_clicks'),
            FieldPanel('track_internally'),
        ], heading=_("Google Analytics")),
        ObjectList([
            FieldPanel('google_site_verification_key'),
        ], heading=_("Google Search")),
    ])
    
    class Meta:
        verbose_name = _("Integration Settings")


@register_setting(icon="site")
class LanguageSettings(BaseSiteSetting):
    default_language = models.CharField(max_length=10, blank=True, null=True, choices=LANGUAGE_CHOICES, default=settings.LANGUAGE_CODE,
                                        verbose_name=_("Default Language"))
    languages = StreamField([
        ('languages', LanguageItemBlock())
    ], blank=True, null=True, use_json_field=True, verbose_name=_("languages"))
    
    panels = [
        FieldPanel('default_language'),
        FieldPanel('languages')
    ]
    
    @cached_property
    def google_languages(self):
        languages = []
        default = LANGUAGE_CHOICES_DICT.get(self.default_language)
        languages.append(default)
        for lang in self.languages:
            languages.append(lang.value.lang_val())
        return languages
    
    class Meta:
        verbose_name = _("Google Translate Languages")
    
    @cached_property
    def included_languages(self):
        return [lang["language"] for lang in self.google_languages]


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
    border_radius = models.IntegerField(validators=[MinValueValidator(0),
                                                    MaxValueValidator(20)], verbose_name=_("Border radius (px)"),
                                        help_text=_("Minimum 0 and Maximum 20 pixels"), default=6)
    box_shadow = models.IntegerField(validators=[MinValueValidator(1),
                                                 MaxValueValidator(24)], verbose_name=_("Box shadow"),
                                     help_text=_("Elevation value minimum 1 and maximum 24"), default=6)
    
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
    
    class Meta:
        verbose_name = _("Navigation Setting")
        verbose_name_plural = _("Navigation Settings")


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
    cap_warnings_list_page = models.ForeignKey(
        'wagtailcore.Page', blank=True, null=True, on_delete=models.SET_NULL, related_name='+',
        verbose_name=_("CAP Warnings List page"))
    
    panels = [
        PageChooserPanel('mailing_list_signup_page'),
        PageChooserPanel('contact_us_page'),
        PageChooserPanel('feedback_page'),
        PageChooserPanel('all_products_page'),
        PageChooserPanel('all_projects_page'),
        PageChooserPanel('all_tenders_page'),
        PageChooserPanel('all_vacancies_page'),
        PageChooserPanel('all_news_page'),
        PageChooserPanel('all_publications_page'),
        PageChooserPanel('all_videos_page'),
        PageChooserPanel('all_applications_page'),
        PageChooserPanel('all_events_page'),
        PageChooserPanel('all_partners_page'),
        PageChooserPanel('cap_warnings_list_page'),
    ]
    
    class Meta:
        verbose_name = _("Important Pages")
        verbose_name_plural = _("Important Pages")


# clear wagtail cache on saving the following models
@receiver(post_save, sender=OrganisationSetting)
@receiver(post_save, sender=IntegrationSettings)
@receiver(post_save, sender=LanguageSettings)
@receiver(post_save, sender=Theme)
@receiver(post_save, sender=NavigationSettings)
@receiver(post_save, sender=ImportantPages)
def handle_clear_wagtail_cache(sender, **kwargs):
    logger.debug("[WAGTAIL_CACHE]: Clearing cache")
    clear_cache()
