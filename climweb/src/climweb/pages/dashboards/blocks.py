from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail import blocks
from climweb.pages.dashboards.snippets import ChartSnippet, DashboardMap
from climweb.base.blocks import TitleTextBlock, TitleTextImageBlock, TableInfoBlock
from django.utils.translation import gettext_lazy as _


class ChartSnippetChooser(blocks.StructBlock):
    charts_block = blocks.ListBlock(SnippetChooserBlock(target_model="dashboards.ChartSnippet"))

    class Meta:
        icon = "chart"
        label = _("Chart")

class MapSnippetChooser(blocks.StructBlock):
    maps_block = blocks.ListBlock(SnippetChooserBlock(target_model="dashboards.DashboardMap"))

    class Meta:
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


