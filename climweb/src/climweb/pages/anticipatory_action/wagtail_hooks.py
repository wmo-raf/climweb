from django.db.models import Q
from django.urls import path
from wagtail import hooks
from wagtail.admin.views.chooser import page_models_from_string
from wagtail.models import Page

from .models import PRODUCT_PAGE_TYPES, UPDATE_PAGE_TYPES, AnticipatoryActionPage
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


def get_page_classes(page_types):
    return set(page_models_from_string(",".join(page_types)))


@hooks.register("construct_page_chooser_queryset")
def narrow_anticipatory_action_choosers(pages, request):
    """
    These choosers allow two page types, so Wagtail opens them at the home page and lists every
    section. Only list the pages that can be chosen, and the pages that lead to them,
    e.g. the news and publications index pages.
    """
    try:
        desired_classes = set(page_models_from_string(request.GET.get("page_type", "")))
    except (ValueError, LookupError):
        return pages
    
    if desired_classes not in (get_page_classes(UPDATE_PAGE_TYPES), get_page_classes(PRODUCT_PAGE_TYPES)):
        return pages
    
    paths = Page.objects.type(*desired_classes).values_list("path", flat=True)
    ancestor_paths = {path[:end] for path in paths for end in range(Page.steplen, len(path), Page.steplen)}
    
    return pages.filter(Q(path__in=ancestor_paths) | Q(pk__in=Page.objects.type(*desired_classes)))
