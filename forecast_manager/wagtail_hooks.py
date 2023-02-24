from django.urls import path, include, reverse
from wagtail.admin.menu import MenuItem
from wagtail.core import hooks
from forecast_manager import urls
from django.utils.html import format_html
from django.templatetags.static import static

class ForecastMenu(MenuItem):
    """
    Registers wagtail-forecast in wagtail admin for superusers.
    """

    def is_shown(self, request):
        return request.user.is_authenticated
        # return request.user.groups.filter(name='Data Managers').exists()


@hooks.register("register_admin_urls")
def register_admin_urls():
    """
    Registers wagtail-forecast urls in the wagtail admin.
    """
    return [
        path(
            "forecast/",
            include((urls, "forecast"), namespace="forecast_admin"),
        ),
        
    ]

@hooks.register("register_admin_menu_item")
def register_forecast_menu():
    """
    Registers wagtail-forecast settings panel in the wagtail admin.
    """
    return ForecastMenu(
        "Forecasts",
        reverse("forecast_admin:upload_forecast"),
        icon_name= 'radio-empty'
    )


@hooks.register("insert_global_admin_css")
def insert_global_admin_css():
    return format_html(
        '<link rel="stylesheet" type="text/css" href="{}">',
        static("css/admin.css"),
    )