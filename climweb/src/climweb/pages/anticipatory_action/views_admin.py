from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from wagtail.models import Page

from climweb.base.models import ImportantPages
from .setup import DEFAULT_SLUG, create_draft_page, get_available_slug


def choose_start(request, parent_page):
    """
    Shown when adding an Anticipatory Action page: start from the template or from a blank page
    """
    site = parent_page.get_site()
    important_pages = ImportantPages.for_site(site) if site else None
    slug = get_available_slug(parent_page)
    
    from_scratch_url = "{}?from_scratch=1".format(
        reverse("wagtailadmin_pages:add", args=["anticipatory_action", "anticipatoryactionpage", parent_page.pk])
    )
    
    return TemplateResponse(request, "anticipatory_action/admin/choose_start.html", {
        "parent_page": parent_page,
        "slug": slug,
        "slug_taken": slug != DEFAULT_SLUG,
        "linked_page": important_pages.anticipatory_action_page if important_pages else None,
        "from_scratch_url": from_scratch_url,
    })


@require_POST
def create_from_template(request, parent_page_id):
    parent_page = get_object_or_404(Page, pk=parent_page_id).specific
    
    if not parent_page.permissions_for_user(request.user).can_add_subpage():
        raise PermissionDenied
    
    page, created = create_draft_page(parent_page, user=request.user)
    if created:
        messages.success(request, _("Draft created from the template. Replace the example content, "
                                    "then publish the page."))
    return redirect("wagtailadmin_pages:edit", page.pk)
