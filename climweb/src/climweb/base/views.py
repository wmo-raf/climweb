from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.translation import gettext as _
from wagtail.admin import messages

from climweb import __version__
from climweb.base.utils import get_latest_cms_release, send_upgrade_command
from climweb.utils.version import check_version_greater_than_current, get_main_version
from .forms import CMSUpgradeForm


def handler500(request):
    context = {}
    response = render(request, "500.html", context=context)
    response.status_code = 500
    return response


def humans(request):
    return render(request, "humans.txt", context={}, content_type="text/plain; charset=utf-8", )


def cms_version_view(request):
    # set upgrade status
    if cache.get("cms_upgrade_pending") is None:
        cache.set("cms_upgrade_pending", False)

    cms_upgrade_pending = cache.get("cms_upgrade_pending")

    template_name = "admin/cms_version.html"
    cms_upgrade_hook_url = getattr(settings, "CMS_UPGRADE_HOOK_URL", None)

    try:
        latest_release = get_latest_cms_release()
        latest_version = latest_release.get("version")
    except Exception as e:
        return render(request, template_name,
                      context={
                          "error": True,
                          "error_message": _("Error fetching latest version. Please try again later."),
                          "error_traceback": str(e)
                      })

    current_version = get_main_version()

    context = {
        "latest_release": latest_release,
        "current_version": current_version,
        "cms_upgrade_hook_url": cms_upgrade_hook_url,
    }

    try:
        latest_release_greater_than_current = check_version_greater_than_current(latest_version)
    except Exception as e:
        return render(request, template_name,
                      context={
                          "error": True,
                          "error_message": _("Error in extracting latest version number from the release"),
                          "error_traceback": str(e)
                      })

    context.update({
        "has_new_version": latest_release_greater_than_current,
    })

    initial = {
        "latest_version": latest_version,
        "current_version": current_version
    }

    form = CMSUpgradeForm(initial=initial)

    context.update({
        "form": form,
    })

    upgrade_form = CMSUpgradeForm(initial=initial)

    if request.POST:
        form = CMSUpgradeForm(request.POST)

        if form.is_valid():
            current_version = form.cleaned_data.get("current_version")
            latest_version = form.cleaned_data.get("latest_version")

            if cms_upgrade_hook_url:
                if cms_upgrade_pending:
                    messages.warning(request, "ClimWeb upgrade already initiated")
                else:
                    try:
                        send_upgrade_command(latest_version)
                        cache.set("cms_upgrade_pending", True)
                        messages.success(request, "ClimWeb upgrade initiated successfully")
                        return redirect("wagtailadmin_home")
                    except Exception as e:
                        cache.set("cms_upgrade_pending", False)
                        messages.error(request, "Error initiating ClimWeb upgrade. Please ensure the "
                                                "'CMS_UPGRADE_HOOK_URL' env variable is working correctly")
                        context.update({
                            "form": upgrade_form
                        })
    else:
        context.update({
            "form": upgrade_form
        })

    context.update({"cms_upgrade_pending": cache.get("cms_upgrade_pending")})

    return render(request, template_name, context=context)


def public_health_check(request):
    return JsonResponse({
        "version": __version__,
    })
