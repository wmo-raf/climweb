import json
import os

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.translation import gettext as _
from wagtail.admin import messages

from django.core.exceptions import ObjectDoesNotExist

from climweb import __version__
from climweb.base.utils import get_latest_cms_release, send_upgrade_command, send_plugin_remove, get_installed_plugins, \
    mix_with_white
from climweb.utils.version import check_version_greater_than_current, get_main_version
from .forms import CMSUpgradeForm
from .models import Theme, OrganisationSetting


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


def plugin_manager_view(request):
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    
    template_name = "admin/plugin_manager.html"
    plugin_manage_hook_url = getattr(settings, "CMS_PLUGIN_MANAGE_HOOK_URL", None)
    plugins = get_installed_plugins()
    
    if request.method == "POST":
        plugin_name = request.POST.get("plugin_name", "").strip()
        if not plugin_name:
            messages.error(request, _("No plugin name provided."))
        elif not plugin_manage_hook_url:
            messages.error(request, _("CMS_PLUGIN_MANAGE_HOOK_URL is not configured."))
        else:
            try:
                send_plugin_remove(plugin_name)
                messages.success(
                    request,
                    _("Plugin '%(name)s' removal initiated. The server will restart shortly.") % {"name": plugin_name},
                )
                return redirect("plugin-manager")
            except Exception:
                messages.error(request,
                               _("Error sending remove command. Check that CMS_PLUGIN_MANAGE_HOOK_URL is reachable."))
    
    return render(request, template_name, context={
        "plugins": plugins,
        "plugin_manage_hook_url": plugin_manage_hook_url,
    })


_DEFAULT_TOKENS = {
    "primary": "#0C447C",
    "primary-light": mix_with_white("#0C447C", 0.75),
    "primary-medium": mix_with_white("#0C447C", 0.50),
    "background": mix_with_white("#0C447C", 0.80),
    "text": "#363636",
    "border-radius": "0.72em",
    "box-shadow-elevation": "6",
}


def _build_tokens():
    try:
        theme = Theme.objects.get(is_default=True)
        primary = theme.primary_hover_color
        return {
            "primary": primary,
            "primary-light": mix_with_white(primary, 0.75),
            "primary-medium": mix_with_white(primary, 0.50),
            "background": mix_with_white(primary, 0.80),
            "text": theme.primary_color,
            "border-radius": f"{theme.border_radius * 0.06}em",
            "box-shadow-elevation": str(theme.box_shadow),
        }
    except ObjectDoesNotExist:
        return _DEFAULT_TOKENS


def style_guide(request):
    try:
        org_setting = OrganisationSetting.for_request(request)
    except Exception:
        org_setting = None
    tokens = _build_tokens()
    context = {
        "tokens": tokens,
        # Flattened aliases so the template avoids hyphenated key access
        "token_primary": tokens["primary"],
        "token_primary_light": tokens["primary-light"],
        "token_primary_medium": tokens["primary-medium"],
        "token_background": tokens["background"],
        "token_text": tokens["text"],
        "token_border_radius": tokens["border-radius"],
        "token_box_shadow": tokens["box-shadow-elevation"],
        "org_setting": org_setting,
    }
    return render(request, "base/style_guide.html", context)


def style_guide_tokens(request):
    return JsonResponse(_build_tokens())


def public_health_check(request):
    return JsonResponse({
        "version": __version__,
    })


def cms_upgrade_status_view(request):
    """
    JSON endpoint polled by the frontend to show live upgrade progress.
    Reads upgrade-status.json written by cms-upgrade.sh into the backup volume.
    """
    backup_dir = settings.DBBACKUP_STORAGE_OPTIONS.get("location", "")
    status_file = os.path.join(backup_dir, "upgrade-status.json")
    
    status_data = {}
    if os.path.exists(status_file):
        try:
            with open(status_file, "r") as f:
                status_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            status_data = {"status": "unknown", "step": "Could not read status file."}
    
    # If the upgrade finished (success or failed), clear the pending flag from cache
    terminal = status_data.get("status") in ("success", "failed")
    if terminal:
        cache.set("cms_upgrade_pending", False)
    
    status_data["cms_upgrade_pending"] = cache.get("cms_upgrade_pending", False)

    return JsonResponse(status_data)
