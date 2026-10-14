from adminboundarymanager.models import AdminBoundarySettings
from django import forms
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.admin.panels import (
    FieldPanel,
    InlinePanel,
    MultiFieldPanel,
    ObjectList,
    PageChooserPanel,
    TabbedInterface,
)
from wagtail.api.v2.utils import get_full_url
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page
from wagtailiconchooser.utils import get_svg_sprite_for_icons

from climweb.base import blocks as base_blocks
from climweb.base.models import AbstractBannerPage
from climweb.config.settings.base import SUMMARY_RICHTEXT_FEATURES
from climweb.pages.events.models import EventPage
from climweb.pages.home.models import RasterFileLayerBlock, WMSLayerBlock, VectorTileLayerBlock
from climweb.pages.news.models import NewsPage
from climweb.pages.publications.models import PublicationPage
from . import blocks as aa_blocks
from .cap import (
    get_active_alert,
    get_alert_display_infos,
    get_hazard_event_type_choices,
    get_matching_active_alerts,
    is_cap_installed,
)


class AnticipatoryActionPageForm(WagtailAdminPageForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "cap_event_types" not in self.fields:
            return

        site = None
        if self.parent_page:
            site = self.parent_page.get_site()

        choices = get_hazard_event_type_choices(site)

        # keep previously selected event types, even if they were since removed from the CAP settings
        selected = self.instance.cap_event_types or []
        known = {value for value, label in choices}
        choices += [(event, event) for event in selected if event not in known]

        self.fields["cap_event_types"] = forms.MultipleChoiceField(
            choices=choices,
            required=False,
            widget=forms.CheckboxSelectMultiple,
            label=self.fields["cap_event_types"].label,
            help_text=self.fields["cap_event_types"].help_text,
            initial=selected,
        )


class AnticipatoryActionPage(AbstractBannerPage):
    template = "anticipatory_action/anticipatory_action_page.html"
    parent_page_types = ["home.HomePage"]
    subpage_types = ["flex_page.FlexPage"]
    max_count = 1
    show_in_menus_default = False
    base_form_class = AnticipatoryActionPageForm

    RISK_LEVEL_CHOICES = (
        ("low", _("Low")),
        ("moderate", _("Moderate")),
        ("high", _("High")),
        ("very_high", _("Very high")),
    )

    PHASE_CHOICES = (
        ("normal", _("Normal")),
        ("watch", _("Watch")),
        ("readiness", _("Readiness")),
        ("activation", _("Activation")),
    )

    # Status
    hazard = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Hazard"),
                              help_text=_("The hazard or climate driver, e.g. Drought, El Niño, Dry spell"))
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, blank=True, null=True,
                                  verbose_name=_("Risk level"))
    affected_areas = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Areas at risk"),
                                      help_text=_("Short list of the areas at risk, e.g. North-eastern counties"))
    show_phase = models.BooleanField(default=False, verbose_name=_("Show anticipatory action phase"),
                                     help_text=_("For services working with a trigger-based anticipatory action "
                                                 "framework. Shows the current phase in the status bar"))
    current_phase = models.CharField(max_length=20, choices=PHASE_CHOICES, default="normal",
                                     verbose_name=_("Current phase"))

    # Situation
    risk_summary_title = models.CharField(max_length=255, default=_("What's happening"),
                                          verbose_name=_("Situation heading"))
    risk_summary = RichTextField(blank=True, null=True, features=SUMMARY_RICHTEXT_FEATURES,
                                 verbose_name=_("Risk summary"),
                                 help_text=_("Plain-language summary: what is happening, the hazard or climate "
                                             "driver involved, the areas, sectors and livelihoods that may be "
                                             "affected, and how the situation is expected to evolve"))
    situation_last_updated = models.DateField(blank=True, null=True, verbose_name=_("Situation last updated"))

    key_facts = StreamField([
        ("key_fact", aa_blocks.KeyFactBlock()),
    ], blank=True, null=True, use_json_field=True, max_num=4, verbose_name=_("Key facts"),
        help_text=_("Up to 4 short figures that sum up the situation, e.g. '40%' below-normal rainfall"))

    recommended_actions = StreamField([
        ("recommended_action", aa_blocks.RecommendedActionBlock()),
    ], blank=True, null=True, use_json_field=True, verbose_name=_("Recommended anticipatory actions"))

    extra_content = StreamField([
        ("title_text", base_blocks.TitleTextBlock()),
        ("title_text_image", base_blocks.TitleTextImageBlock()),
        ("accordion", base_blocks.AccordionBlock()),
        ("table", base_blocks.TableInfoBlock()),
    ], blank=True, null=True, use_json_field=True, verbose_name=_("Additional content"))

    # Map
    map_title = models.CharField(max_length=255, default=_("Where"), verbose_name=_("Map heading"))
    map_layers = StreamField([
        ("raster_file_layer", RasterFileLayerBlock(label=_("Raster Layer"), icon="map")),
        ("wms_layer", WMSLayerBlock(label=_("WMS Layer"), icon="map")),
        ("vector_tile_layer", VectorTileLayerBlock(label=_("Vector Tile Layer"), icon="map")),
    ], blank=True, null=True, use_json_field=True, verbose_name=_("Map Layers"),
        help_text=_("Risk and monitoring products to show on the map, "
                    "e.g. drought indices, vegetation or rainfall anomalies"))

    # CAP
    show_cap_alerts = models.BooleanField(default=True, verbose_name=_("Show related CAP warnings"))
    cap_event_types = models.JSONField(default=list, blank=True, verbose_name=_("CAP hazard types"),
                                       help_text=_("Only show warnings for these hazard types. "
                                                   "Leave empty to show all hazard types"))
    cap_areas = StreamField([
        ("boundary_block", aa_blocks.AreaOfInterestBoundaryBlock(label=_("Admin Boundary"))),
        ("polygon_block", aa_blocks.AreaOfInterestPolygonBlock(label=_("Draw Polygon"))),
    ], blank=True, null=True, use_json_field=True, verbose_name=_("CAP areas of interest"),
        help_text=_("Only show warnings whose area overlaps any of these areas. Leave empty to show all areas"))
    featured_cap_alert = models.ForeignKey(
        "wagtailcore.Page", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        verbose_name=_("Featured CAP warning"),
        help_text=_("Optional. Shown first while it is active, even if it does not match the filters above"))

    # Links
    institutions_heading = models.CharField(max_length=255, default=_("Preparedness and response"),
                                            verbose_name=_("Institutions heading"))
    institutions = StreamField([
        ("institution", aa_blocks.InstitutionLinkBlock()),
    ], blank=True, null=True, use_json_field=True, verbose_name=_("Institutions"))

    content_panels = Page.content_panels + [
        *AbstractBannerPage.content_panels,
        MultiFieldPanel([
            FieldPanel("hazard"),
            FieldPanel("risk_level"),
            FieldPanel("affected_areas"),
            FieldPanel("situation_last_updated"),
            FieldPanel("show_phase"),
            FieldPanel("current_phase"),
        ], heading=_("Status")),
        MultiFieldPanel([
            FieldPanel("risk_summary_title"),
            FieldPanel("risk_summary"),
            FieldPanel("key_facts"),
        ], heading=_("What's happening")),
    ]

    actions_panels = [
        FieldPanel("recommended_actions"),
        FieldPanel("extra_content"),
    ]

    map_panels = [
        FieldPanel("map_title"),
        FieldPanel("map_layers"),
    ]

    cap_panels = [
        FieldPanel("show_cap_alerts"),
        FieldPanel("cap_event_types"),
        FieldPanel("cap_areas"),
        PageChooserPanel("featured_cap_alert", page_type="cap.CapAlertPage"),
    ] if is_cap_installed() else []

    links_panels = [
        InlinePanel("products", heading=_("Products"), label=_("Product")),
        MultiFieldPanel([
            FieldPanel("institutions_heading"),
            FieldPanel("institutions"),
        ], heading=_("Institutions")),
        InlinePanel("applications", heading=_("Applications"), label=_("Application")),
    ]

    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading=_("Content")),
        ObjectList(actions_panels, heading=_("Actions")),
        ObjectList(map_panels + cap_panels, heading=_("Map & Warnings")),
        ObjectList(links_panels, heading=_("Products & Links")),
        ObjectList(AbstractBannerPage.promote_panels, heading=_("Promote")),
        ObjectList(AbstractBannerPage.settings_panels, heading=_("Settings")),
    ])

    class Meta:
        verbose_name = _("Anticipatory Action Page")
        verbose_name_plural = _("Anticipatory Action Pages")

    @cached_property
    def listing_image(self):
        return self.banner_image

    @property
    def has_status(self):
        return bool(self.hazard or self.risk_level or self.affected_areas or self.show_phase)

    @property
    def phases(self):
        """
        Phases in order, each marked as past, current or upcoming, for the phase indicator
        """
        current_index = [value for value, label in self.PHASE_CHOICES].index(self.current_phase)
        phases = []
        for index, (value, label) in enumerate(self.PHASE_CHOICES):
            if index < current_index:
                state = "past"
            elif index == current_index:
                state = "current"
            else:
                state = "upcoming"
            phases.append({"value": value, "label": label, "state": state})
        return phases

    @property
    def action_audiences(self):
        audiences = []
        for block in self.recommended_actions or []:
            audience = block.value.get("audience")
            if audience and audience not in audiences:
                audiences.append(audience)
        return audiences

    @cached_property
    def product_pages(self):
        return [item.product.specific for item in self.products.select_related("product")
                if item.product and item.product.live]

    @cached_property
    def events(self):
        return EventPage.objects.live().filter(
            is_anticipatory_action=True, is_archived=False, is_hidden=False).order_by("-date_from")[:3]

    @cached_property
    def latest_updates(self):
        news = list(NewsPage.objects.live().filter(is_anticipatory_action=True).order_by("-is_featured", "-date")[:2])

        # fill up to 4 items with publications
        publications = PublicationPage.objects.live().filter(is_anticipatory_action=True).order_by(
            "-featured", "-publication_date")[:4 - len(news)]

        return news + list(publications)

    @cached_property
    def cap_area_geometries(self):
        geometries = []
        for area in self.cap_areas or []:
            geometry = area.value.geometry
            if geometry is not None:
                geometries.append(geometry)
        return geometries

    @cached_property
    def active_featured_cap_alert(self):
        return get_active_alert(self.featured_cap_alert_id)

    @cached_property
    def active_cap_alerts(self):
        if not self.show_cap_alerts:
            return []
        return get_matching_active_alerts(self)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        map_layer_icons = ["warning", "layer-group"]
        map_layer_icons.extend([layer.value.get("icon") for layer in self.map_layers or [] if layer.value.get("icon")])
        
        context.update({
            "country_bounds": AdminBoundarySettings.for_request(request).combined_countries_bounds,
            "map_layer_svg_sprite": get_svg_sprite_for_icons(map_layer_icons),
            "map_settings_url": get_full_url(request, reverse("anticipatory-action-map-settings",
                                                              args=[self.pk])),
            "active_alert_infos": get_alert_display_infos(self.active_cap_alerts, request),
            "show_warnings": is_cap_installed() and self.show_cap_alerts,
        })

        return context


class AnticipatoryActionProduct(Orderable):
    page = ParentalKey(AnticipatoryActionPage, on_delete=models.CASCADE, related_name="products")
    product = models.ForeignKey("wagtailcore.Page", on_delete=models.CASCADE, related_name="+",
                                verbose_name=_("Product"))

    panels = [
        PageChooserPanel("product", page_type=["products.ProductPage", "products.SubNationalProductPage"]),
    ]


class AnticipatoryActionApplication(Orderable):
    page = ParentalKey(AnticipatoryActionPage, on_delete=models.CASCADE, related_name="applications")
    application = models.ForeignKey("base.Application", on_delete=models.CASCADE, verbose_name=_("Application"))
