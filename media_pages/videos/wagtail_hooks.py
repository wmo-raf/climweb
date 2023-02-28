from django.urls import re_path, include
from django.urls import reverse
from wagtail.admin.menu import MenuItem
from wagtail import hooks
from wagtail.snippets.permissions import user_can_edit_snippet_type

from . import urls as video_urls
from .models import YoutubePlaylist


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        re_path(r'^videos/', include(video_urls)),
    ]


class VideoMenuItem(MenuItem):
    def is_shown(self, request):
        return user_can_edit_snippet_type(request.user, YoutubePlaylist)


@hooks.register('register_admin_menu_item')
def register_styleguide_menu_item():
    return VideoMenuItem(
        ('Videos'),
        reverse('playlist_view'),
        classnames='icon icon-fa-youtube',
        order=1000
    )