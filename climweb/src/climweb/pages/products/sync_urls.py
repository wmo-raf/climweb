from django.urls import path

from . import sync_api

urlpatterns = [
    path("setup.sh", sync_api.setup_script, name="product_sync_setup_script"),
    path("setup/exchange/", sync_api.setup_exchange, name="product_sync_exchange"),
    path("ping/", sync_api.ping, name="product_sync_ping"),
    path("upload/", sync_api.upload, name="product_sync_upload"),
]
