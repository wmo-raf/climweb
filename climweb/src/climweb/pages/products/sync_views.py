"""
The CMS-side setup panel.

The point of this screen is that an editor never explains anything technical to
the met service. They click a button, and hand over one command.
"""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from wagtail.admin.auth import user_passes_test

from .models import ProductPage
from .sync_api import product_formats, resolve_watch_root
from .sync_models import ProductSyncCredential, ProductSyncSetupCode


def can_manage_product_sync(user):
    return user.is_superuser or user.has_perm("wagtailadmin.access_admin")


def product_edit_url(product):
    """
    Link to the Product snippet's own edit page.

    Every unmet item on this screen is fixed there, so without a link the editor
    has to know that Products live under Snippets and go looking.

    The URL name is derived from the model rather than hardcoded, and a failure
    to reverse it returns an empty string: if the snippet registration ever
    changes, the button should disappear rather than break the whole page.
    """
    opts = product._meta
    try:
        return reverse(
            f"wagtailsnippets_{opts.app_label}_{opts.model_name}:edit",
            args=[product.pk],
        )
    except NoReverseMatch:
        return ""


@user_passes_test(can_manage_product_sync)
def product_sync_setup_for_product_view(request, product_id):
    """
    Reach the setup screen from the Product snippet listing.

    The setup view is keyed on the ProductPage, because that is what the
    ingester publishes to. A snippet row only knows its own pk, so resolve the
    page here rather than making the listing aware of pages.
    """
    product_pages = ProductPage.objects.filter(product_id=product_id).live()
    product_page = product_pages.first()

    if product_page is None:
        messages.warning(
            request,
            "This product has no published product page yet, so there is "
            "nowhere for files to be published to. Create and publish a "
            "Product page for it first.",
        )
        # They arrived from the listing, so the referer is almost always right.
        # Fall back to the admin home rather than guessing a snippet URL name.
        return redirect(
            request.META.get("HTTP_REFERER") or reverse("wagtailadmin_home")
        )

    return redirect(reverse("product_sync_setup", args=[product_page.pk]))


@user_passes_test(can_manage_product_sync)
def product_sync_setup_view(request, product_page_id):
    product_page = get_object_or_404(ProductPage, pk=product_page_id)
    product = product_page.product

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "generate":
            ProductSyncSetupCode.issue(product, user=request.user)
            messages.success(
                request,
                "New setup code generated. Any code sent out previously will no "
                "longer work.",
            )

        elif action == "request_full_sync":
            credential = ProductSyncCredential.objects.filter(
                pk=request.POST.get("credential_id"), product=product
            ).first()
            if credential and credential.is_active:
                credential.request_full_sync()
                messages.success(
                    request,
                    f"{credential.label} will send every file the next time it "
                    "checks in. Servers check every 10 minutes, so this usually "
                    "happens within a few minutes.",
                )

        elif action == "cancel_full_sync":
            credential = ProductSyncCredential.objects.filter(
                pk=request.POST.get("credential_id"), product=product
            ).first()
            if credential:
                credential.cancel_full_sync()
                messages.success(request, "Request cancelled.")

        elif action == "revoke":
            credential = ProductSyncCredential.objects.filter(
                pk=request.POST.get("credential_id"), product=product
            ).first()
            if credential:
                credential.revoke()
                messages.success(
                    request,
                    f"Disconnected {credential.label}. That server can no longer "
                    "send files.",
                )

        return redirect(reverse("product_sync_setup", args=[product_page.pk]))

    active_code = (
        ProductSyncSetupCode.objects.filter(product=product, used_at__isnull=True)
        .order_by("-created_at")
        .first()
    )
    if active_code and not active_code.is_valid:
        active_code = None

    setup_url = request.build_absolute_uri("/").rstrip("/")
    formats = product_formats(product)

    # Everything the product needs before any of this can work. Showing these
    # as a checklist here saves a round of "we set it up but nothing appears".
    readiness = [
        {
            "label": "Auto-ingestion is enabled",
            "ok": bool(product.ingestion_enabled),
            "fix": "Tick 'Enable Auto-Ingestion' on this product.",
        },
        {
            "label": "Variable name is set",
            "ok": bool(product.variable_name),
            "fix": "Set a Variable Name on this product, e.g. weekly_rainfall.",
            "value": product.variable_name,
        },
        {
            "label": "Watch root is set",
            "ok": bool(product.watch_root),
            "fix": "Set a Watch Root Path on this product.",
            "value": resolve_watch_root(product.watch_root) if product.watch_root else "",
        },
        {
            "label": "At least one file format is configured",
            "ok": bool(formats),
            "fix": "Add a category with a File Format, e.g. pdf.",
            "value": ", ".join(formats),
        },
    ]
    ready = all(item["ok"] for item in readiness)

    return render(
        request,
        "products/product_sync_setup.html",
        {
            "product_page": product_page,
            "product": product,
            "product_page_url": product_page.url,
            "product_edit_url": product_edit_url(product),
            "active_code": active_code,
            "command": (
                f"curl -fsSL {setup_url}/api/product-sync/setup.sh "
                f"| sudo bash -s {active_code.code}"
            )
            if active_code
            else "",
            "credentials": ProductSyncCredential.objects.filter(product=product),
            "readiness": readiness,
            "ready": ready,
            "formats": formats,
        },
    )
