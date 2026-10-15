import json

from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from shapely.geometry import shape
from wagtail import blocks
from wagtail.blocks import StructValue
from wagtail.blocks.stream_block import StreamBlockValidationError
from wagtail.blocks.struct_block import StructBlockValidationError
from wagtail.images.blocks import ImageChooserBlock
from wagtailiconchooser.blocks import IconChooserBlock

from climweb.config.settings.base import SUMMARY_RICHTEXT_FEATURES


class PhaseBlock(blocks.StructBlock):
    label = blocks.CharBlock(max_length=30, label=_("Phase name"), help_text=_("e.g. Watch, Ready, Alarm"))
    description = blocks.CharBlock(max_length=200, required=False, label=_("What it means"),
                                   help_text=_("Shown under the phases when this phase is current, "
                                               "e.g. Trigger reached, partners are preparing activities"))
    is_current = blocks.BooleanBlock(required=False, label=_("Current phase"))
    
    class Meta:
        icon = "list-ol"
        label = _("Phase")


class PhasesBlock(blocks.StreamBlock):
    phase = PhaseBlock()
    
    class Meta:
        max_num = 6
    
    def clean(self, value):
        value = super().clean(value)
        current = [child for child in value if child.value.get("is_current")]
        if len(current) > 1:
            raise StreamBlockValidationError(non_block_errors=ErrorList([
                ValidationError(_("Only one phase can be the current phase"))
            ]))
        return value


def default_phases():
    """
    Phases for services without their own framework. Editors can rename, add or remove phases,
    e.g. Ready / Set / Go, or Normal / Alert / Alarm / Emergency / Recovery
    """
    return [
        ("phase", {"label": str(_("Normal")), "description": "", "is_current": True}),
        ("phase", {"label": str(_("Watch")), "description": "", "is_current": False}),
        ("phase", {"label": str(_("Readiness")), "description": "", "is_current": False}),
        ("phase", {"label": str(_("Activation")), "description": "", "is_current": False}),
    ]


class KeyFactBlock(blocks.StructBlock):
    value = blocks.CharBlock(max_length=20, label=_("Figure"), help_text=_("e.g. 40%, 1.2M, 3 months"))
    label = blocks.CharBlock(max_length=100, label=_("What it means"),
                             help_text=_("e.g. below-normal rainfall expected"))
    
    class Meta:
        icon = "pick"
        label = _("Key fact")


class RecommendedActionBlock(blocks.StructBlock):
    audience = blocks.CharBlock(max_length=100, label=_("Who should act"),
                                help_text=_("Sector or group this applies to, e.g. Farmers, Pastoralists, "
                                            "Water authorities, General public"))
    icon = IconChooserBlock(required=False, label=_("Icon"))
    actions = blocks.RichTextBlock(features=SUMMARY_RICHTEXT_FEATURES, label=_("Recommended actions"))

    class Meta:
        icon = "list-ul"
        label = _("Recommended actions")


class InstitutionLinkStructValue(StructValue):
    @cached_property
    def url(self):
        page = self.get("page")
        if page:
            return page.url
        return self.get("external_url")

    @cached_property
    def is_external(self):
        return not self.get("page") and bool(self.get("external_url"))


class InstitutionLinkBlock(blocks.StructBlock):
    name = blocks.CharBlock(max_length=255, label=_("Name"))
    description = blocks.TextBlock(required=False, label=_("Role in preparedness and response"))
    logo = ImageChooserBlock(required=False, label=_("Logo"))
    page = blocks.PageChooserBlock(required=False, label=_("Page on this website"))
    external_url = blocks.URLBlock(required=False, label=_("External link"),
                                   help_text=_("Used if no page on this website is selected"))

    class Meta:
        icon = "site"
        label = _("Institution")
        value_class = InstitutionLinkStructValue

    def clean(self, value):
        value = super().clean(value)
        if not value.get("page") and not value.get("external_url"):
            raise StructBlockValidationError(block_errors={
                "external_url": ValidationError(_("Select a page on this website or provide an external link"))
            })
        return value


class AreaOfInterestStructValue(StructValue):
    @cached_property
    def geometry(self):
        geom = self.get("boundary") or self.get("polygon")
        if not geom:
            return None
        return shape(json.loads(geom))

    @cached_property
    def name(self):
        return self.get("areaDesc")


if "capcomposer.capeditor" in settings.INSTALLED_APPS:
    from capcomposer.capeditor.blocks import BoundaryFieldBlock, PolygonOrMultiPolygonFieldBlock


    class AreaOfInterestBoundaryBlock(blocks.StructBlock):
        class Meta:
            value_class = AreaOfInterestStructValue

        areaDesc = blocks.TextBlock(label=_("Area/Region Name"))
        boundary = BoundaryFieldBlock(label=_("Boundary"), help_text=_("Click to select boundary on the map"))


    class AreaOfInterestPolygonBlock(blocks.StructBlock):
        class Meta:
            value_class = AreaOfInterestStructValue

        areaDesc = blocks.TextBlock(label=_("Area/Region Name"))
        polygon = PolygonOrMultiPolygonFieldBlock(label=_("Polygon"), help_text=_("Draw custom area on the map"))
else:
    class AreaOfInterestBoundaryBlock(blocks.StructBlock):
        class Meta:
            value_class = AreaOfInterestStructValue

        areaDesc = blocks.TextBlock(label=_("Area/Region Name"))


    class AreaOfInterestPolygonBlock(blocks.StructBlock):
        class Meta:
            value_class = AreaOfInterestStructValue

        areaDesc = blocks.TextBlock(label=_("Area/Region Name"))
