from django.urls import re_path, include
from wagtail import hooks

from . import urls as zoom_events_urls


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        re_path(r'^zoom/', include(zoom_events_urls)),
    ]