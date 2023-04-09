from wagtail.contrib.modeladmin.options import (
    ModelAdmin, 
    modeladmin_register,
)
from site_settings.models import Theme

class ThemeSettings(ModelAdmin):
    model = Theme
    menu_label = 'Themes'
    menu_icon = 'cog'
    menu_order = 200
    add_to_settings_menu = True
    exclude_from_explorer = False
    # inspect_view_enabled = True

modeladmin_register(ThemeSettings)