from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    modeladmin_register,
    
)

from wagtailcache.cache import clear_cache

from base.models import Theme
from adminboundarymanager.wagtail_hooks import AdminBoundaryManagerAdminGroup


@hooks.register('insert_global_admin_css')
def global_admin_css():
    return format_html('<link rel="stylesheet" href="{}">', static('css/admin.css'))


    
modeladmin_register(AdminBoundaryManagerAdminGroup)


class ThemeSettings(ModelAdmin):
    model = Theme
    menu_label = _('Themes')
    menu_icon = 'cog'
    menu_order = 950
    add_to_settings_menu = True
    exclude_from_explorer = False


modeladmin_register(ThemeSettings)


@hooks.register('after_create_page')
@hooks.register('after_edit_page')
def clear_wagtailcache(request, page):
    if page.live:
        clear_cache()


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
