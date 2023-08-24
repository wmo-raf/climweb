from django.conf import settings
from django.shortcuts import render

from base.forms import CMSUpgradeForm
from base.utils import get_latest_cms_release, send_upgrade_command
from wagtail.admin import messages
from django.core.cache import cache


def handler500(request):
    context = {}
    response = render(request, "500.html", context=context)
    response.status_code = 500
    return response


def cms_version_view(request):
    # set upgrade status
    if cache.get("cms_upgrade_pending") is None:
        cache.set("cms_upgrade_pending", False)

    cms_upgrade_pending = cache.get("cms_upgrade_pending")

    template_name = "admin/cms_version.html"
    current_version = getattr(settings, "CMS_VERSION", None)
    cms_upgrade_hook_url = getattr(settings, "CMS_UPGRADE_HOOK_URL", None)

    try:
        latest_release = get_latest_cms_release()
    except Exception:
        latest_release = None

    context = {
        "current_version": current_version,
        "cms_upgrade_hook_url": cms_upgrade_hook_url
    }

    if latest_release and current_version:
        context.update({
            "latest_release": latest_release
        })

    if request.POST:
        form = CMSUpgradeForm(request.POST)

        if form.is_valid():
            current_version = form.cleaned_data.get("current_version")
            latest_version = form.cleaned_data.get("latest_version")

            if cms_upgrade_hook_url:
                if cms_upgrade_pending:
                    messages.warning(request, "CMS upgrade already initiated")
                else:
                    try:
                        send_upgrade_command(latest_version)
                        cache.set("cms_upgrade_pending", True)
                        messages.success(request, "CMS upgrade initiated successfully")
                    except Exception:
                        cache.set("cms_upgrade_pending", False)
                        messages.error(request, "Error initiating upgrade")
    else:
        initial = {
            "latest_version": latest_release.get("version"),
            "current_version": current_version
        }
        form = CMSUpgradeForm(initial=initial)

        context.update({
            "form": form,
        })

    context.update({"cms_upgrade_pending": cms_upgrade_pending})

    return render(request, template_name, context=context)
