from django.urls import reverse
from wagtail.contrib.modeladmin.options import (
    ModelAdmin, 
    modeladmin_register,
    ModelAdminGroup
)
from site_settings.models import Theme
from forecast_manager.models import City, ConditionCategory
from layer_manager.models import WMSRequest, LayerCategory, Legend
from wagtail.admin.menu import MenuItem

class ThemeSettings(ModelAdmin):
    model = Theme
    menu_label = 'Themes'
    menu_icon = 'cog'
    menu_order = 200
    add_to_settings_menu = True
    exclude_from_explorer = False
    # inspect_view_enabled = True

modeladmin_register(ThemeSettings)

class CitiesAdmin(ModelAdmin):
    model = City
    menu_label = 'Cities'
    menu_icon = 'cog'
    add_to_settings_menu = False
    exclude_from_explorer = False

class ConditionCategoryAdmin(ModelAdmin):
    model = ConditionCategory
    menu_label = 'Weather Conditions'
    menu_icon = 'cog'
    add_to_settings_menu = False
    exclude_from_explorer = False

class CityForecastGroup(ModelAdminGroup):
    menu_label = 'City Forecast'
    menu_icon = 'table'  # change as required
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    items = (CitiesAdmin, ConditionCategoryAdmin)

    def get_submenu_items(self):
        menu_items = []
        item_order = 1
        for modeladmin in self.modeladmin_instances:
            menu_items.append(modeladmin.get_menu_item(order=item_order))
            item_order += 1

            # append raster upload link
        upload_menu_item = MenuItem(label="Forecasts", url=reverse("forecast_admin:add_forecast"), icon_name="cog")

        menu_items.append(upload_menu_item)

        return menu_items

modeladmin_register(CityForecastGroup)

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


modeladmin_register(LayerManagerGroup)