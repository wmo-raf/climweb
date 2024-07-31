from pages.aviation.models import Station, StationCategory
from wagtail.snippets.views.snippets import (
    SnippetViewSet,
    SnippetViewSetGroup,
)
from django.utils.translation import gettext_lazy as _
from wagtail.snippets.models import register_snippet
from django.urls import path
from django.urls import reverse
from wagtail.admin.menu import MenuItem

from wagtail import hooks
from pages.aviation.views import add_message, load_aviation_stations

@hooks.register("register_admin_urls")
def register_admin_urls():
    """
    Registers forecast urls in the wagtail admin.
    """
    return [
        path("add-message/", add_message, name="add_message"),
        path('load-aviation-stations/', load_aviation_stations, name='load_aviation_stations'),

    ]

class StationCategoriesViewSet(SnippetViewSet):
    model = StationCategory
    icon = "globe"
    menu_label = _("Station Categories")



class StationsViewSet(SnippetViewSet):
    model = Station
    icon = 'location'
    menu_label = _('Stations')

    list_display = ('name', 'category')
    list_filter = {"name": ["icontains"]}
    index_template_name = "aviation/station_index.html"


class StationsViewSetGroup(SnippetViewSetGroup):
    items = (StationsViewSet,StationCategoriesViewSet)
    menu_icon = "airport"
    menu_label = _("Aviation Editor")
    menu_name = "aviation_editor"
    menu_order = 200

    def get_submenu_items(self):
        menu_items = super().get_submenu_items()

        try:
            add_message_item = MenuItem(label=_("Messages"), url=reverse("add_message"), icon_name="plus")

            menu_items.append(add_message_item)
        except Exception:
            pass

        return menu_items



register_snippet(StationsViewSetGroup)