from django.urls import path
from wagtail import hooks

from .models import AnticipatoryActionPage
from .views_admin import choose_start, create_from_template


@hooks.register("register_admin_urls")
def register_anticipatory_action_urls():
    return [
        path("anticipatory-action/create-from-template/<int:parent_page_id>/", create_from_template,
             name="anticipatory_action_create_from_template"),
    ]


@hooks.register("before_create_page")
def offer_anticipatory_action_template(request, parent_page, page_class):
    if page_class is not AnticipatoryActionPage:
        return None
    
    # the blank form, after choosing "create from scratch" or when the form is submitted
    if request.method != "GET" or request.GET.get("from_scratch"):
        return None
    
    return choose_start(request, parent_page)
