from climweb.pages.dashboards.forms import BoundaryMultiPolygonField
from wagtail import hooks
from django import forms

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
    menu_order = 102
    add_to_settings_menu = False
    list_display = ("title", "chart_type", "area_desc")
    list_filter = ("chart_type", "area_desc")
    search_fields = ("title", "area_desc")


class MapAdmin(ModelAdmin):
    model = DashboardMap
    menu_label = "Maps"
    menu_icon = "site"
    menu_order = 101
    add_to_settings_menu = False
    list_display = ("title","map_layer","area_desc")
    list_filter = ("area_desc", )
    search_fields = ("title",  "area_desc")


class DashboardPageAdmin(ModelAdmin):
    model = DashboardPage
    menu_label = "Dashboards"
    menu_icon = "report"
    menu_order = 100
    add_to_settings_menu = False
    list_display = ("title",)
    search_fields = ("title",)


class CustomDashboardMenu(ModelAdminGroup):
    menu_label = "Atlas"
    menu_icon = "analysis"
    menu_order = 105
    items = (ChartAdmin, MapAdmin, DashboardPageAdmin)


modeladmin_register(CustomDashboardMenu)


class DashboardMapForm(forms.ModelForm):
    boundary = BoundaryMultiPolygonField(required=False)

    class Meta:
        model = DashboardMap
        fields = "__all__"

@hooks.register('construct_snippet_form')
def use_custom_form_for_map_snippet(model, request, **kwargs):
    if model == DashboardMap:
        return DashboardMapForm