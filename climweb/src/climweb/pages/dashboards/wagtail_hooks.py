from wagtail import hooks
from wagtail_modeladmin.options import (
    ModelAdmin, modeladmin_register, ModelAdminGroup
)
from .snippets import ChartSnippet, DashboardMap
from .models import DashboardPage
from django.templatetags.static import static
from django.utils.html import format_html

@hooks.register('insert_editor_js')
def chart_snippet_editor_js():
    return format_html('<script src="{}"></script>', static('js/chart_snippet.js'))
class ChartAdmin(ModelAdmin):
    model = ChartSnippet
    menu_label = "Charts"
    menu_icon = "chart"
    menu_order = 100
    add_to_settings_menu = False
    list_display = ("title", "chart_type", "dataset")
    search_fields = ("title",)


class MapAdmin(ModelAdmin):
    model = DashboardMap
    menu_label = "Maps"
    menu_icon = "site"
    menu_order = 101
    add_to_settings_menu = False
    list_display = ("title","map_layer")
    search_fields = ("title",)


class DashboardPageAdmin(ModelAdmin):
    model = DashboardPage
    menu_label = "Dashboards"
    menu_icon = "report"
    menu_order = 102
    add_to_settings_menu = False
    list_display = ("title",)
    search_fields = ("title",)


class CustomDashboardMenu(ModelAdminGroup):
    menu_label = "Dashboards"
    menu_icon = "analysis"
    menu_order = 105
    items = (ChartAdmin, MapAdmin, DashboardPageAdmin)


modeladmin_register(CustomDashboardMenu)


