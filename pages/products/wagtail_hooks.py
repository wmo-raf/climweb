from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin import widgets as wagtail_admin_widgets

from .models import ProductPage
from .views import product_layers_integration_view


@hooks.register('register_admin_urls')
def urlconf_products():
    return [
        path('product-layers-integration/<int:product_page_id>', product_layers_integration_view,
             name="product_layer_integration"),
    ]


@hooks.register('register_page_listing_buttons')
def page_listing_buttons(page, page_perms, next_url=None):
    if isinstance(page, ProductPage):
        url = reverse("product_layer_integration", args=[page.pk, ])
        yield wagtail_admin_widgets.PageListingButton(
            "MapViewer Integration",
            url,
            priority=50
        )
