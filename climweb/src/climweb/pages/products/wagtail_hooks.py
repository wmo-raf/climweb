from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin import widgets as wagtail_admin_widgets

from .models import ProductPage
from .views import product_layers_integration_view, trigger_product_ingestion_view


@hooks.register('register_admin_urls')
def urlconf_products():
    return [
        path('product-layers-integration/<int:product_page_id>', product_layers_integration_view,
             name="product_layer_integration"),
        path('product-run-ingestion/<int:product_page_id>', trigger_product_ingestion_view,
             name="product_run_ingestion"),
    ]


@hooks.register('register_page_listing_buttons')
def page_listing_buttons(page, user, next_url=None):
    if isinstance(page, ProductPage):
        yield wagtail_admin_widgets.PageListingButton(
            "MapViewer Integration",
            reverse("product_layer_integration", args=[page.pk]),
            priority=50,
        )
        if page.product.ingestion_enabled:
            yield wagtail_admin_widgets.PageListingButton(
                "Run Ingestion",
                reverse("product_run_ingestion", args=[page.pk]),
                priority=60,
            )
