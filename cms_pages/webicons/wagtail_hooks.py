from django.urls import include, path
from django.urls import reverse
from django.utils.html import format_html
# from django.utils.translation import ugettext
from wagtail.admin.menu import MenuItem
from wagtail.admin.search import SearchArea
from wagtail import hooks

from . import urls as icon_urls
from .forms import GroupIconPermissionFormSet
from .models import WebIcon
from .permissions import permission_policy


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        path('webicons/', include(icon_urls)),
    ]


class IconsMenuItem(MenuItem):
    def is_shown(self, request):
        return permission_policy.user_has_any_permission(
            request.user, ['add', 'change', 'delete']
        )


@hooks.register('register_admin_menu_item')
def register_styleguide_menu_item():
    return IconsMenuItem(
        ('SVG Icons'),
        reverse('webicons:index'),
        icon_name= 'radio-empty',
        order=500
    )


@hooks.register('insert_editor_js')
def editor_js():
    return format_html(
        """
        <script>
            window.chooserUrls.iconChooser = '{0}';
        </script>
        """,
        reverse('webicons:chooser')
    )


class IconsSearchArea(SearchArea):
    def is_shown(self, request):
        return permission_policy.user_has_any_permission(
            request.user, ['add', 'change', 'delete']
        )


@hooks.register('register_admin_search_area')
def register_images_search_area():
    return IconsSearchArea(
        ('Icons'), reverse('webicons:index'),
        name='icons',
        classnames='icon icon-image',
        order=300)


@hooks.register('register_group_permission_panel')
def register_image_permissions_panel():
    return GroupIconPermissionFormSet


@hooks.register('describe_collection_contents')
def describe_collection_docs(collection):
    icons_count = WebIcon.objects.filter(collection=collection).count()
    if icons_count:
        url = reverse('webicons:index') + ('?collection_id=%d' % collection.id)
        return {
            'count': icons_count,
            # 'count_text': ugettext(
            #     "%(count)s icon",
            #     "%(count)s icons",
            #     icons_count
            # ) % {'count': icons_count},
            'url': url,
        }
