from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail import blocks
from climweb.pages.dashboards.snippets import ChartSnippet, DashboardMap
from climweb.base.blocks import TitleTextBlock, TitleTextImageBlock, TableInfoBlock
from django.utils.translation import gettext_lazy as _


class ChartSnippetChooser(blocks.StructBlock):
    charts_block = blocks.ListBlock(SnippetChooserBlock(target_model="dashboards.ChartSnippet"))

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)

        maps_with_urls = []
        for chart_snippet in value.get("charts_block", []):
            maps_with_urls.append({
                "chart": chart_snippet,
            })

        context["charts"] = maps_with_urls
        return context
    

    class Meta:
        template = "streams/dashboard_chart.html"
        icon = "chart"
        label = _("Chart")

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
        ("title_text",TitleTextBlock(icon="document")),
        ("title_text_image",TitleTextImageBlock(icon="image")),
        ("chart", ChartSnippetChooser()),
        ("map", MapSnippetChooser()),
        ("table",TableInfoBlock(icon="table"))
    ], required=True)

    

    class Meta:
        icon = "folder-open-inverse"
        label = "Dashboard Section"


