from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from wagtail.admin.auth import user_passes_test

from .forms import ProductLayerForm
from .models import ProductPage


@user_passes_test(lambda u: u.is_superuser or u.has_perm('wagtailadmin.access_admin'))
def trigger_product_ingestion_view(request, product_page_id):
    product_page = get_object_or_404(ProductPage, pk=product_page_id)
    product = product_page.product

    if not product.ingestion_enabled:
        messages.warning(request, f"Auto-ingestion is not enabled for {product.name}.")
        return redirect(request.META.get('HTTP_REFERER', '/admin/'))

    try:
        from climweb.pages.products.tasks import _ingest_product
        _ingest_product(product)
        messages.success(request, f"Ingestion completed for {product.name}.")
    except Exception as exc:
        messages.error(request, f"Ingestion failed for {product.name}: {exc}")

    return redirect(request.META.get('HTTP_REFERER', '/admin/'))


def product_layers_integration_view(request, product_page_id):
    template_name = "products/product_layer_integration.html"
    product_page = ProductPage.objects.get(pk=product_page_id)

    form = ProductLayerForm(instance=product_page)

    context = {
        "form_media": form.media,
        "product_page_url": product_page.url
    }

    if request.POST:
        form = ProductLayerForm(request.POST, instance=product_page)

        # save data
        if form.is_valid():
            form.save()

    context.update({
        "form": form,
    })

    return render(request, template_name, context=context)
