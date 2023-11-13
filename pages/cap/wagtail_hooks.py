from capeditor.models import CapSetting
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem, Menu
from wagtail_modeladmin.menus import GroupMenuItem
from wagtail_modeladmin.options import (
    ModelAdmin,
    modeladmin_register,
    ModelAdminGroup
)

from .models import CapAlertPage, CAPGeomanagerSettings
from .utils import create_cap_geomanager_dataset


class CAPAdmin(ModelAdmin):
    model = CapAlertPage
    menu_label = _('Alerts')
    menu_icon = 'list-ul'
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False


class CAPMenuGroupAdminMenuItem(GroupMenuItem):
    def is_shown(self, request):
        return request.user.has_perm("base.can_view_alerts_menu")


class CAPMenuGroup(ModelAdminGroup):
    menu_label = _('CAP Alerts')
    menu_icon = 'warning'  # change as required
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    items = (CAPAdmin,)

    def get_menu_item(self, order=None):
        if self.modeladmin_instances:
            submenu = Menu(items=self.get_submenu_items())
            return CAPMenuGroupAdminMenuItem(self, self.get_menu_order(), submenu)

    def get_submenu_items(self):
        menu_items = []
        item_order = 1

        for modeladmin in self.modeladmin_instances:
            menu_items.append(modeladmin.get_menu_item(order=item_order))
            item_order += 1

        try:

            # add settings menu
            settings_url = reverse(
                "wagtailsettings:edit",
                args=[CapSetting._meta.app_label, CapSetting._meta.model_name, ],
            )
            gm_settings_menu = MenuItem(label=_("Settings"), url=settings_url, icon_name="cog")
            menu_items.append(gm_settings_menu)

            # add geomanager settings menu

            settings_url = reverse("wagtailsettings:edit",
                                   args=[CAPGeomanagerSettings._meta.app_label,
                                         CAPGeomanagerSettings._meta.model_name, ], )

            cap_geomanager_settings_menu = MenuItem(label=_("Geomanager Settings"), url=settings_url, icon_name="cog")

            menu_items.append(cap_geomanager_settings_menu)

        except Exception:
            pass

        return menu_items


modeladmin_register(CAPMenuGroup)


@hooks.register('construct_settings_menu')
def hide_settings_menu_item(request, menu_items):
    hidden_settings = ["cap-geomanager-settings"]
    menu_items[:] = [item for item in menu_items if item.name not in hidden_settings]


@hooks.register('register_geomanager_datasets')
def add_geomanager_datasets(request):
    datasets = []
    cap_geomanager_settings = CAPGeomanagerSettings.for_request(request)
    if cap_geomanager_settings.show_on_mapviewer and cap_geomanager_settings.geomanager_subcategory:

        # check if we have any live alerts
        has_live_alerts = CapAlertPage.objects.live().exists()

        # create dataset
        dataset = create_cap_geomanager_dataset(cap_geomanager_settings, has_live_alerts, request)

        # add dataset to list
        if dataset:
            datasets.append(dataset)

    return datasets
