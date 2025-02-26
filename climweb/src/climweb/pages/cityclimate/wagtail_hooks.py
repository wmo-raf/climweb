from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin import widgets as wagtail_admin_widgets

from .models import CityClimateDataPage
from .views import (
    load_city_climate_data,
    pre_load_climate_data,
    confirm_delete_city_climate_data,
    delete_city_climate_date,
    view_city_climate_data
)


@hooks.register('register_admin_urls')
def urlconf_boundarymanager():
    return [
        path('cityclimate/cities-checklist/<int:page_id>', pre_load_climate_data, name='cityclimate_data_checklist'),
        path('cityclimate/load-data/<int:page_id>/<uuid:city_id>/', load_city_climate_data,
             name='cityclimate_load_data'),
        path('cityclimate/view/<int:page_id>/<uuid:city_id>/', view_city_climate_data, name='view_city_climate_data'),
        path('cityclimate/delete/<int:page_id>/<uuid:city_id>/delete/', delete_city_climate_date,
             name='delete_city_climate_date'),
        path('cityclimate/delete/<int:page_id>/<uuid:city_id>/', confirm_delete_city_climate_data,
             name='confirm_delete_city_climate_data'),
    ]


@hooks.register('register_page_listing_buttons')
def page_listing_buttons(page, page_perms, next_url=None):
    if isinstance(page, CityClimateDataPage):
        url = reverse("cityclimate_data_checklist", args=[page.pk, ])
        yield wagtail_admin_widgets.PageListingButton(
            "Load Data",
            url,
            priority=50
        )
