from django.urls import path
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import (
    SnippetViewSet,
    SnippetViewSetGroup,
)

from .models import Airport, AirportCategory
from .views import add_message, load_aviation_airports


@hooks.register("register_admin_urls")
def register_admin_urls():
    return [
        path("add-message/", add_message, name="add_message"),
        path('load-aviation-airports/', load_aviation_airports, name='load_aviation_airports'),
    ]


class AirportCategoriesViewSet(SnippetViewSet):
    model = AirportCategory
    icon = "globe"
    menu_label = _("Airport Categories")


class AirportsViewSet(SnippetViewSet):
    model = Airport
    icon = 'location'
    menu_label = _('Airports')

    list_display = ('name', 'category')
    list_filter = {"name": ["icontains"]}
    index_template_name = "aviation/airport_index.html"


class AirportsViewSetGroup(SnippetViewSetGroup):
    items = (AirportsViewSet, AirportCategoriesViewSet)
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


register_snippet(AirportsViewSetGroup)
