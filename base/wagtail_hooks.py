from django.conf import settings
from django.templatetags.static import static
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.ui.components import Component
from wagtail_modeladmin.options import (
    ModelAdmin,
    modeladmin_register,

)
from wagtailcache.cache import clear_cache

from base.models import Theme
from base.views import cms_version_view


@hooks.register('insert_global_admin_css')
def global_admin_css():
    return format_html('<link rel="stylesheet" href="{}">', static('css/admin.css'))


@hooks.register('register_admin_urls')
def urlconf_base():
    return [
        path('cms-version', cms_version_view, name='cms-version'),
    ]


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


@hooks.register('after_edit_snippet')
def clear_cache_after_snippet_edit(request, snippet):
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


class CMSUpgradeNotificationPanel(Component):
    name = "cms_upgrade_notification"
    template_name = "admin/cms_upgrade_notification.html"
    order = 100

    def get_current_version(self):
        return getattr(settings, "CMS_VERSION", None)

    def get_webhook_url(self):
        return getattr(settings, "CMS_UPGRADE_HOOK_URL", None)

    def has_required_variables(self):
        current_version = self.get_current_version()
        webhook_url = self.get_webhook_url()

        return current_version and webhook_url

    def get_context_data(self, parent_context):
        current_version = self.get_current_version()
        if current_version:
            return {
                "current_version": current_version,
                "latest_release_url": "https://api.github.com/repos/wmo-raf/nmhs-cms/releases/latest",
                "version_upgrade_url": reverse("cms-version")
            }
        return {}

    def render_html(self, parent_context):
        print(self.has_required_variables())
        if (
                parent_context["request"].user.is_superuser
                and self.has_required_variables()
        ):
            return super().render_html(parent_context)
        else:
            return ""


@hooks.register('construct_homepage_panels')
def add_another_welcome_panel(request, panels):
    panels.append(CMSUpgradeNotificationPanel())
