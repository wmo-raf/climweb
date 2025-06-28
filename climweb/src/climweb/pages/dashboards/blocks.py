from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail import blocks
from climweb.pages.dashboards.snippets import ChartSnippet, DashboardMap

class ChartSnippetChooser(blocks.StructBlock):
    charts_block = blocks.ListBlock(SnippetChooserBlock(target_model="dashboards.ChartSnippet"))

class MapSnippetChooser(blocks.StructBlock):
    maps_block = blocks.ListBlock(SnippetChooserBlock(target_model="dashboards.DashboardMap"))


class DashboardSectionBlock(blocks.StructBlock):
    section_title = blocks.CharBlock(required=True)

    content = blocks.StreamBlock([
        ("charts", ChartSnippetChooser()),
        ("maps", MapSnippetChooser()),
    ], required=True)


    class Meta:
        icon = "folder-open-inverse"
        label = "Dashboard Section"


