import re

from django.conf import settings

if "capcomposer.cap" in settings.INSTALLED_APPS:
    from capcomposer.cap.utils import get_currently_active_alerts
from django.contrib import messages
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.db.models import CharField, TextField
from django.http import HttpResponseRedirect
from django.templatetags.static import static
from django.urls import path, reverse
from django.utils.html import format_html, strip_tags
from django.utils.translation import gettext_lazy as _
from better_profanity import profanity
from wagtail import hooks
from wagtail.fields import RichTextField, StreamField
from wagtail.rich_text import RichText
from wagtail.admin.ui.components import Component
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail_modeladmin.options import (
    ModelAdmin,
    modeladmin_register, ModelAdminGroup,
)
from wagtailcache.cache import clear_cache

from climweb.utils.version import get_main_version, check_version_greater_than_current
from .cap import create_cap_geomanager_dataset
from .models import Theme, ServiceCategory, CAPGeomanagerSettings
from .utils import get_latest_cms_release
from .views import cms_version_view, plugin_manager_view, cms_upgrade_status_view
from .cap_views import create_alert_from_geometry
from .backups.views import (
    google_drive_connect,
    google_drive_callback,
    google_drive_disconnect,
    run_backup_now,
    backup_help,
    sftp_generate_key,
    sftp_clear_key,
    sftp_clear_hostkey,
    backup_browser,
    backup_download,
)
from .logs.views import log_viewer, log_fetch, log_download
from .task_health.views import task_health


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
    urls = [
        path('cms-version', cms_version_view, name='cms-version'),
        path('cms-upgrade-status', cms_upgrade_status_view, name='cms-upgrade-status'),
        path('plugins', plugin_manager_view, name='plugin-manager'),
        path('backup/google/connect', google_drive_connect, name='backup-google-connect'),
        path('backup/google/callback', google_drive_callback, name='backup-google-callback'),
        path('backup/google/disconnect', google_drive_disconnect, name='backup-google-disconnect'),
        path('backup/run-now', run_backup_now, name='backup-run-now'),
        path('backup/help', backup_help, name='backup-help'),
        path('backup/sftp/generate-key', sftp_generate_key, name='backup-sftp-generate-key'),
        path('backup/sftp/clear-key', sftp_clear_key, name='backup-sftp-clear-key'),
        path('backup/sftp/clear-hostkey', sftp_clear_hostkey, name='backup-sftp-clear-hostkey'),
        path('backup/browse', backup_browser, name='backup-browser'),
        path('backup/download', backup_download, name='backup-download'),
        path('logs', log_viewer, name='log-viewer'),
        path('logs/fetch', log_fetch, name='log-fetch'),
        path('logs/download', log_download, name='log-download'),
        path('task-health', task_health, name='task-health'),
    ]

    if "capcomposer.cap" in settings.INSTALLED_APPS:
        urls.append(
            path('cap/create-from-geometry/', create_alert_from_geometry,
                 name='cap_alert_create_from_geometry'),
        )

    return urls


@hooks.register('register_settings_menu_item')
def register_plugin_manager_menu_item():
    from wagtail.admin.menu import MenuItem
    return MenuItem(
        _('Plugins'),
        reverse('plugin-manager'),
        icon_name='cog',
        order=960,
    )


@hooks.register('register_settings_menu_item')
def register_log_viewer_menu_item():
    from wagtail.admin.menu import MenuItem

    class LogViewerMenuItem(MenuItem):
        def is_shown(self, request):
            # Logs regularly contain data ordinary editors have no business
            # seeing, so this stays superuser-only — and stays hidden entirely
            # on instances that aren't running the socket proxy.
            from .logs.docker_client import is_enabled

            return bool(is_enabled() and request.user.is_superuser)

    return LogViewerMenuItem(
        _('Server logs'),
        reverse('log-viewer'),
        icon_name='doc-full-inverse',
        order=970,
    )


@hooks.register('register_settings_menu_item')
def register_task_health_menu_item():
    from wagtail.admin.menu import MenuItem

    class TaskHealthMenuItem(MenuItem):
        def is_shown(self, request):
            # Tracebacks can carry request data, so superuser-only like the logs.
            return bool(request.user.is_superuser)

    return TaskHealthMenuItem(
        _('Task health'),
        reverse('task-health'),
        icon_name='tasks',
        order=975,
    )


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


# Optional extra terms for this platform (e.g. domain-specific abuse).
# better-profanity's built-in list already covers common profanity and
# leet-speak variants; add words here that are specific to ClimWeb.
_EXTRA_TERMS = getattr(settings, "CLIMWEB_BLOCKED_TERMS", [
    "kill yourself", "go die", "you should die",
    "bomb threat", "death threat",
])

profanity.load_censor_words()
if _EXTRA_TERMS:
    profanity.add_censor_words(_EXTRA_TERMS)


def _richtext_to_text(source):
    """Strip HTML from a rich text source string, keeping words that sit on either side
    of a tag from being glued together (e.g. "<p>Foo</p><p>Bar</p>" should not become
    "FooBar")."""
    if not source:
        return ""
    # Replace tags with a space rather than deleting them outright.
    spaced = re.sub(r"<[^>]+>", " ", str(source))
    return strip_tags(spaced)


def _stream_value_text(value, parts):
    """Recursively collect only genuine author-written text from a StreamField/StructBlock/
    ListBlock value tree, without ever rendering the stream to HTML.

    Calling str()/render on a StreamValue executes its block templates, which pulls in CSS
    classes, SVG icon markup, image URLs, and other markup noise into the scanned text. That
    markup is mostly punctuation-separated "words" with no real relationship to each other,
    and better-profanity treats any two such adjacent tokens as candidates for its multi-word
    blocked phrases (e.g. "bomb threat"), producing false positives that have nothing to do
    with what the editor actually typed. Walking the raw block values instead means only real
    field content (headings, titles, rich text) ever reaches the profanity check.
    """
    if value is None:
        return

    if isinstance(value, RichText):
        text = _richtext_to_text(value.source)
        if text.strip():
            parts.append(text)
        return

    if isinstance(value, str):
        if value.strip():
            parts.append(value)
        return

    # StructValue behaves like a dict of child block values.
    if hasattr(value, "values") and callable(value.values):
        for child in value.values():
            _stream_value_text(child, parts)
        return

    # StreamValue / ListValue and plain lists/tuples of child blocks.
    if hasattr(value, "__iter__"):
        for item in value:
            # StreamValue iterates over StreamChild objects; unwrap to the actual value.
            _stream_value_text(getattr(item, "value", item), parts)
        return

    # Anything else (images, documents, pages, URLs, choosers, numbers, etc.) is not
    # user-authored text and is intentionally skipped.


def _page_text(page):
    """Collect all author-written text from every CharField, TextField, RichTextField, and
    StreamField on the specific page type, for the harassment-content profanity check."""
    specific = page.specific
    parts = [specific.title or ""]
    for field in specific._meta.get_fields():
        if not isinstance(field, (CharField, TextField, RichTextField, StreamField)):
            continue
        if field.name == "title":
            continue
        value = getattr(specific, field.name, None)
        if not value:
            continue
        if isinstance(field, StreamField):
            _stream_value_text(value, parts)
        elif isinstance(field, RichTextField):
            text = _richtext_to_text(value)
            if text.strip():
                parts.append(text)
        else:
            parts.append(str(value))
    # Join with newlines rather than spaces: better-profanity's multi-word phrase matching
    # (used by our custom terms like "bomb threat") requires an exact single-space separator
    # to combine two tokens, so a newline here prevents two unrelated words from separate
    # fields (e.g. one block's heading and the next block's heading) from being coincidentally
    # read as a single blocked phrase, while a real phrase typed together within one field is
    # unaffected since it still contains its own literal space.
    return "\n".join(parts)


_LETTER_RE = re.compile(r"[^\W\d_]", re.UNICODE)


def _drop_letterless_tokens(text):
    """Remove tokens that contain no letters at all before the profanity check.

    better-profanity normalises leet-speak by mapping digits onto letters (7->t,
    3->e, 5->s, 1->i, 0->o, 4->a). Machine-generated numeric strings therefore
    decode into words by coincidence: a CAP area polygon coordinate such as
    "-1.73375" splits on the period and the fragment "73375" normalises to
    "teets", which is in the default word list. An alert with a drawn area
    carries hundreds of such coordinates, so publishing fails at random.

    Tokens with no letters are never author-written prose, so dropping them
    removes the false positives. Genuine leet-speak evasion ("sh1t", "@ss")
    always retains at least one letter and is still checked.
    """
    if not text:
        return ""

    return "\n".join(
        " ".join(token for token in line.split() if _LETTER_RE.search(token))
        for line in text.split("\n")
    )


# Page types the harassment check never blocks, as "app_label.ModelName".
#
# CAP alerts are exempt because a blocked publish means a weather warning does
# not reach the public — a far worse outcome than an unfiltered word slipping
# through. Their content is also a poor fit for a general-purpose profanity
# filter: emergency vocabulary overlaps it, and the areas carry machine-generated
# geometry that decodes into blocked words by coincidence (see
# _drop_letterless_tokens). Alerts are authored by accredited NMHS staff and
# reviewed through the CAP workflow, so the editorial safeguard sits elsewhere.
_HARASSMENT_CHECK_EXEMPT_PAGE_TYPES = {
    page_type.lower()
    for page_type in getattr(
        settings,
        "CLIMWEB_HARASSMENT_CHECK_EXEMPT_PAGE_TYPES",
        ["cap.CapAlertPage"],
    )
}


def _is_exempt_from_harassment_check(page):
    specific_class = page.specific_class or type(page)
    page_type = f"{specific_class._meta.app_label}.{specific_class.__name__}"
    return page_type.lower() in _HARASSMENT_CHECK_EXEMPT_PAGE_TYPES


@hooks.register("before_publish_page")
def block_harmful_content_on_publish(request, page):
    if _is_exempt_from_harassment_check(page):
        return

    text = _drop_letterless_tokens(_page_text(page))
    if profanity.contains_profanity(text):
        messages.error(
            request,
            _(
                "This page could not be published because it contains content "
                "that violates the ClimWeb Harassment Protection Policy. "
                "Please review and edit the page before publishing."
            ),
        )
        return HttpResponseRedirect(
            request.headers.get("Referer", reverse("wagtailadmin_home"))
        )


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
        'wagtailfontawesomesvg/brands/tiktok.svg',
        'wagtailfontawesomesvg/solid/phone.svg',
        'wagtailfontawesomesvg/solid/box-archive.svg',
        'wagtailfontawesomesvg/solid/hourglass-start.svg',
        'wagtailfontawesomesvg/solid/hourglass-end.svg',
        'wagtailfontawesomesvg/solid/hourglass-half.svg',
        'wagtailfontawesomesvg/solid/wallet.svg',
        'wagtailfontawesomesvg/solid/table-list.svg',
        'wagtailfontawesomesvg/solid/table-cells.svg',
        'wagtailfontawesomesvg/solid/grip.svg',
        'wagtailfontawesomesvg/solid/sitemap.svg',
        'wagtailfontawesomesvg/solid/timeline.svg',
        'wagtailfontawesomesvg/solid/circle-nodes.svg',
        'wagtailfontawesomesvg/solid/hashtag.svg',
        'wagtailfontawesomesvg/solid/map-pin.svg',
    ]
    
    others = [
        'wagtailfontawesomesvg/solid/podcast.svg',
        "icons/empty-tray.svg",
        "icons/x-twitter.svg",
        "icons/dam.svg",
        "icons/dust-storm.svg"
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


@hooks.register("register_permissions")
def register_2fa_permission():
    """Keep "Enable 2FA" selectable in Settings -> Groups.

    wagtail-2fa only registers this permission when it finds the literal string
    "wagtail_2fa.middleware.VerifyUserPermissionsMiddleware" in MIDDLEWARE. We
    run a subclass under our own path, so that check fails and the permission
    would quietly vanish from the group editor — leaving no way to require 2FA
    of anyone other than superusers.
    """
    return Permission.objects.filter(
        content_type__app_label="wagtailadmin", codename="enable_2fa"
    )


@hooks.register('construct_main_menu')
def hide_menu_items(request, menu_items):
    custom_menu_permissions = {
        "geo-manager": "base.can_view_geomanager_menu",
        "city_forecast": "base.can_view_forecast_menu",
    }
    
    hidden = []
    
    for item in menu_items:
        if custom_menu_permissions.get(item.name) and not request.user.has_perm(custom_menu_permissions.get(item.name)):
            hidden.append(item.name)
    
    menu_items[:] = [item for item in menu_items if item.name not in hidden]


# @hooks.register('construct_settings_menu')
# def hide_settings_menu_item(request, menu_items):
#     hidden_settings = ["cap-geomanager-settings"]
#     menu_items[:] = [item for item in menu_items if item.name not in hidden_settings]


if "capcomposer.cap" in settings.INSTALLED_APPS:
    @hooks.register('register_geomanager_datasets')
    def add_geomanager_datasets(request):
        datasets = []
        cap_geomanager_settings = CAPGeomanagerSettings.for_request(request)
        if cap_geomanager_settings.show_on_mapviewer and cap_geomanager_settings.geomanager_subcategory:

            # check if we have any active alerts
            has_live_alerts = get_currently_active_alerts().exists()

            # create dataset
            dataset = create_cap_geomanager_dataset(cap_geomanager_settings, has_live_alerts, request)

            # add dataset to list
            if dataset:
                datasets.append(dataset)

        return datasets
