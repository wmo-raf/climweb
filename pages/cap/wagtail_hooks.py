from wagtail.contrib.modeladmin.options import modeladmin_register
from .models import CapAlertPage
from capeditor.models import CapSetting
from wagtail.contrib.modeladmin.options import (
    ModelAdmin, 
    modeladmin_register,
    ModelAdminGroup
)
from adminboundarymanager.wagtail_hooks import AdminBoundaryManagerAdminGroup
from django.urls import path, include, reverse
from wagtail.admin.menu import MenuItem
from django.utils.translation import gettext_lazy as _

modeladmin_register(AdminBoundaryManagerAdminGroup)

class CAPAdmin(ModelAdmin):
    model = CapAlertPage
    menu_label = 'Alerts'
    menu_icon = 'list-ul'
    menu_order = 200 
    add_to_settings_menu = False
    exclude_from_explorer = False



class CAPMenuGroup(ModelAdminGroup):
    menu_label = 'CAP Alerts'
    menu_icon = 'warning'  # change as required
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    items = (CAPAdmin,)

    def get_submenu_items(self):
        menu_items = []
        item_order = 1
        
        for modeladmin in self.modeladmin_instances:
            menu_items.append(modeladmin.get_menu_item(order=item_order))
            item_order += 1
            
        try:
            settings_url = reverse(
                "wagtailsettings:edit",
                args=[CapSetting._meta.app_label, CapSetting._meta.model_name, ],
            )
            gm_settings_menu = MenuItem(label=_("Settings"), url=settings_url, icon_name="cog")
            menu_items.append(gm_settings_menu)
        except Exception:
            pass

        return menu_items


modeladmin_register(CAPMenuGroup)