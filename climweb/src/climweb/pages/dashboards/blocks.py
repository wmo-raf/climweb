from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail import blocks
from climweb.base.blocks import  TextOnlyBlock, TitleOnlyBlock, TitleTextBlock, TitleTextImageBlock, TableInfoBlock, WhatWeDoGroupBlock, AccordionBlock
from django.utils.translation import gettext_lazy as _
from climweb.base import blocks as climweb_blocks
from geomanager.models import RasterFileLayer
from wagtail_color_panel.blocks import NativeColorBlock

class ChartSnippetChooser(blocks.StructBlock):
    charts_block = blocks.ListBlock(SnippetChooserBlock(target_model="dashboards.ChartSnippet"))
    
    class Meta:
        template = "streams/dashboard_chart.html"
        icon = "chart"
        label = _("Chart")

class MultiVariableChartSnippetChooser(blocks.StructBlock):
    multivariable_charts_block = blocks.ListBlock(SnippetChooserBlock(target_model="dashboards.MultiVariableChartSnippet"))
    
    class Meta:
        template = "streams/dashboard_multivariable_chart.html"
        icon = "chart"
        label = _("Multi-Variable Chart")

class MapSnippetChooser(blocks.StructBlock):
    maps_block = blocks.ListBlock(SnippetChooserBlock(target_model="dashboards.DashboardMap"))

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        request = context.get("request")

        maps_with_urls = []
        for map_snippet in value.get("maps_block", []):
            maps_with_urls.append({
                "map": map_snippet,
                "layertimestampsurl": map_snippet.get_layertimestampsurl(request),
                "datasetsurl": map_snippet.get_datasetsurl(request),
                "boundary_tiles_url": map_snippet.get_boundary_tiles_url(request),
                "bounds": map_snippet.get_bounds(request),
            })

        context["maps"] = maps_with_urls
        return context
    
    class Meta:
        template = "streams/dashboard_map.html"
        icon = "site"
        label = _("Map")


class DashboardSectionBlock(blocks.StructBlock):
    section_title = blocks.CharBlock(required=True)

    content = blocks.StreamBlock([
        ("title_only",TitleOnlyBlock()),
        ("text_only",TextOnlyBlock()),
        ("title_text",TitleTextBlock(icon="document")),
        ("title_text_image",TitleTextImageBlock(icon="image")),
        ("chart", ChartSnippetChooser()),
        ("multivariable_chart", MultiVariableChartSnippetChooser()),
        ("map", MapSnippetChooser()),
        ("table",TableInfoBlock(icon="table")),
        ("what_we_do", WhatWeDoGroupBlock()),
        ("accordion", AccordionBlock(icon="layer-group")),
    ], required=True)

    class Meta:
        icon = "folder-open-inverse"
        label =  _("Dashboard Section")


class ChartVariableBlock(blocks.StructBlock):

    CHART_TYPE_CHOICES = [
        ("line",  _("Line Chart")),
        ("column",  _("Vertical Bar Chart")),
        ("bar",  _("Horizontal Bar Chart")),
        ("area",  _("Area Chart")),
        ("scatter",  _("Scatter Plot")),
    ]

    chart_variable = blocks.CharBlock(required=True, label=_("Chart variable name"))
    chart_color = NativeColorBlock(required=False, default="#0b76e1", label=_("Chart color"))
    chart_type = blocks.ChoiceBlock(choices=CHART_TYPE_CHOICES, default="line", label=_("Chart type"))
    dataset = climweb_blocks.UUIDModelChooserBlock(RasterFileLayer, icon="table")
    data_unit = blocks.CharBlock(required=False, label=_("Data unit"))
    
    class Meta:
        icon = "cogs"
        label = _("Chart Variable")
