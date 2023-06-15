from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    modeladmin_register
)

from base.models import Theme


class ThemeSettings(ModelAdmin):
    model = Theme
    menu_label = 'Themes'
    menu_icon = 'cog'
    menu_order = 950
    add_to_settings_menu = True
    exclude_from_explorer = False


modeladmin_register(ThemeSettings)
