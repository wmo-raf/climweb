from django.urls import path, include, reverse
from wagtail.admin.menu import MenuItem
from wagtail import hooks
from forecast_manager import urls
from django.utils.html import format_html
from django.templatetags.static import static
from forecast_manager.models import City, ConditionCategory

from wagtail.contrib.modeladmin.options import (
    ModelAdmin, 
    modeladmin_register,
    ModelAdminGroup
)
# class ForecastMenu(MenuItem):
#     """
#     Registers wagtail-forecast in wagtail admin for superusers.
#     """

#     def is_shown(self, request):
#         return request.user.is_authenticated
        # return request.user.groups.filter(name='Data Managers').exists()


@hooks.register("register_admin_urls")
def register_admin_urls():
    """
    Registers wagtail-forecast urls in the wagtail admin.
    """
    return [
        path(
            "forecast/",
            include((urls, "forecast"), namespace="forecast_admin"),
        ),
        
    ]

# @hooks.register("register_admin_menu_item")
# def register_forecast_menu():
#     """
#     Registers wagtail-forecast settings panel in the wagtail admin.
#     """
#     return ForecastMenu(
#         "Forecasts",
#         reverse("forecast_admin:add_forecast"),
#         icon_name= 'table'
#     )


@hooks.register("insert_global_admin_css")
def insert_global_admin_css():
    return format_html(
        '<link rel="stylesheet" type="text/css" href="{}">',
        static("css/admin.css"),
    )


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