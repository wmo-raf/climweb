from django.conf import settings
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.templatetags.static import static
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.ui.components import Component
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail_modeladmin.options import (
    ModelAdmin,
    modeladmin_register, ModelAdminGroup,
)
from wagtailcache.cache import clear_cache

from climweb.utils.version import get_main_version, check_version_greater_than_current
from .models import Theme, ServiceCategory
from .utils import get_latest_cms_release
from .views import cms_version_view


class ModelAdminGroupWithHiddenItems(ModelAdminGroup):
    def get_submenu_items(self):
        menu_items = []
        item_order = 1
        for model_admin in self.modeladmin_instances:
            if hasattr(model_admin, "hidden") and not model_admin.hidden:
                menu_items.append(model_admin.get_menu_item(order=item_order))
                item_order += 1
        return menu_items


@hooks.register('insert_global_admin_css')
def global_admin_css():
    return format_html('<link rel="stylesheet" href="{}">', static('css/admin.css'))


@hooks.register('register_admin_urls')
def urlconf_base():
    return [
        path('cms-version', cms_version_view, name='cms-version'),
    ]


class ServiceViewSet(SnippetViewSet):
    model = ServiceCategory


register_snippet(ServiceViewSet)


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
@hooks.register('after_delete_page')
def clear_wagtailcache(request, page):
    if page.live:
        clear_cache()
        cache.clear()


@hooks.register('after_create_snippet')
@hooks.register('after_create_snippet')
@hooks.register('after_delete_snippet')
def clear_cache_after_snippet_edit(request, snippet):
    clear_cache()
    cache.clear()


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
        'wagtailfontawesomesvg/solid/podcast.svg',
        "icons/empty-tray.svg",
        "icons/x-twitter.svg"
    ]

    return icons + brands + others


class CMSUpgradeNotificationPanel(Component):
    name = "cms_upgrade_notification"
    template_name = "admin/cms_upgrade_notification.html"
    order = 100

    def get_webhook_url(self):
        return getattr(settings, "CMS_UPGRADE_HOOK_URL", None)

    def has_required_variables(self):
        current_version = get_main_version()
        webhook_url = self.get_webhook_url()

        return current_version and webhook_url

    def get_context_data(self, parent_context):
        current_version = get_main_version()
        try:
            latest_release = get_latest_cms_release()
            latest_version = latest_release.get("version")
            latest_release_greater_than_current = check_version_greater_than_current(latest_version)

            return {
                "has_new_version": latest_release_greater_than_current,
                "latest_release": latest_release,
                "current_version": current_version,
                "cms_upgrade_hook_url": self.get_webhook_url(),
                "version_upgrade_url": reverse("cms-version")
            }
        except Exception as e:
            pass

        return {}

    def render_html(self, parent_context):
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


@hooks.register("register_permissions")
def register_permissions():
    return Permission.objects.filter(content_type__app_label="base")


@hooks.register('construct_main_menu')
def hide_menu_items(request, menu_items):
    custom_menu_permissions = {
        "geo-manager": "base.can_view_geomanager_menu",
        "city_forecast": "base.can_view_forecast_menu",
        "aviation_editor": "base.can_view_aviation_editor_menu",
    }

    hidden = []

    for item in menu_items:
        if custom_menu_permissions.get(item.name) and not request.user.has_perm(custom_menu_permissions.get(item.name)):
            hidden.append(item.name)

    menu_items[:] = [item for item in menu_items if item.name not in hidden]
