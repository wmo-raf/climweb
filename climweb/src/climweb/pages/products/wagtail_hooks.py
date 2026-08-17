from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin import widgets as wagtail_admin_widgets

from climweb.base.models import Product

from .models import ProductPage
from .sync_views import (can_manage_product_sync,
                         product_sync_setup_for_product_view,
                         product_sync_setup_view)
from .views import product_layers_integration_view, trigger_product_ingestion_view


@hooks.register('register_admin_urls')
def urlconf_products():
    return [
        path('product-layers-integration/<int:product_page_id>', product_layers_integration_view,
             name="product_layer_integration"),
        path('product-run-ingestion/<int:product_page_id>', trigger_product_ingestion_view,
             name="product_run_ingestion"),
        path('product-sync-setup/<int:product_page_id>', product_sync_setup_view,
             name="product_sync_setup"),
        # Entry point from the Product snippet listing, which knows the snippet
        # pk but not the page it is published through.
        path('product-sync-setup/for-product/<int:product_id>',
             product_sync_setup_for_product_view,
             name="product_sync_setup_for_product"),
    ]


@hooks.register('register_page_listing_buttons')
def page_listing_buttons(page, user, next_url=None):
    if isinstance(page, ProductPage):
        yield wagtail_admin_widgets.PageListingButton(
            "MapViewer Integration",
            reverse("product_layer_integration", args=[page.pk]),
            priority=50,
        )
        yield wagtail_admin_widgets.PageListingButton(
            "AutoPublish",
            reverse("product_sync_setup", args=[page.pk]),
            priority=55,
        )
        if page.product.ingestion_enabled:
            yield wagtail_admin_widgets.PageListingButton(
                "Run Ingestion",
                reverse("product_run_ingestion", args=[page.pk]),
                priority=60,
            )


@hooks.register('register_snippet_listing_buttons')
def snippet_listing_buttons(snippet, user, next_url=None):
    """
    Reach automated publishing straight from Snippets -> Products.

    Editors configure a product here, so this is where they look next. The link
    goes through the by-product view, which resolves the ProductPage; the button
    is shown even when no page exists yet, so that case gets an explanation
    rather than a missing button to wonder about.
    """
    if isinstance(snippet, Product) and can_manage_product_sync(user):
        yield wagtail_admin_widgets.ListingButton(
            "AutoPublish",
            reverse("product_sync_setup_for_product", args=[snippet.pk]),
            priority=10,
        )
