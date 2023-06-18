from wagtail import hooks
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


@hooks.register("register_icons")
def register_icons(icons):
    brands = [
        'wagtailfontawesomesvg/brands/facebook.svg',
        'wagtailfontawesomesvg/brands/instagram.svg',
        'wagtailfontawesomesvg/brands/youtube.svg',
        'wagtailfontawesomesvg/brands/medium.svg',
        'wagtailfontawesomesvg/brands/github.svg',
        'wagtailfontawesomesvg/brands/twitter.svg',
        'wagtailfontawesomesvg/brands/linkedin.svg',
        'wagtailfontawesomesvg/brands/soundcloud.svg',
        'wagtailfontawesomesvg/brands/flickr.svg',
        'wagtailfontawesomesvg/brands/telegram.svg',
        'wagtailfontawesomesvg/brands/whatsapp.svg',
    ]

    others = [
        'wagtailfontawesomesvg/solid/podcast.svg'
    ]

    return icons + brands + others
