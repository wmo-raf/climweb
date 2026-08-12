"""
The CMS-side setup panel.

The point of this screen is that an editor never explains anything technical to
the met service. They click a button, and hand over one command.
"""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from wagtail.admin.auth import user_passes_test

from .models import ProductPage
from .sync_api import product_formats, resolve_watch_root
from .sync_models import ProductSyncCredential, ProductSyncSetupCode


def _can_manage(user):
    return user.is_superuser or user.has_perm("wagtailadmin.access_admin")


@user_passes_test(_can_manage)
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
