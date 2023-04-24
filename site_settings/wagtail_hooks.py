from django.urls import reverse
from wagtail.contrib.modeladmin.options import (
    ModelAdmin, 
    modeladmin_register,
    ModelAdminGroup
)
from site_settings.models import Theme
from layer_manager.models import WMSRequest, LayerCategory, Legend

class ThemeSettings(ModelAdmin):
    model = Theme
    menu_label = 'Themes'
    menu_icon = 'cog'
    menu_order = 950
    add_to_settings_menu = True
    exclude_from_explorer = False
    # inspect_view_enabled = True


class WMSRequestAdmin(ModelAdmin):
    model = WMSRequest
    menu_label = 'WMS Request'
    menu_icon = 'cog'
    add_to_settings_menu = False
    exclude_from_explorer = False

class LegendAdmin(ModelAdmin):
    model = Legend
    menu_label = 'Legend'
    menu_icon = 'cog'
    add_to_settings_menu = False
    exclude_from_explorer = False

class LayerCategoryAdmin(ModelAdmin):
    model = LayerCategory
    menu_label = 'Layer Categories'
    menu_icon = 'cog'
    add_to_settings_menu = False
    exclude_from_explorer = False


class LayerManagerGroup(ModelAdminGroup):
    menu_label = 'Layer Manager'
    menu_icon = 'cog'  # change as required
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    items = (LegendAdmin, LayerCategoryAdmin, WMSRequestAdmin)

modeladmin_register(ThemeSettings)

modeladmin_register(LayerManagerGroup)