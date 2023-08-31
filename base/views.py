from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render, redirect
from django.urls import reverse
from wagtail.admin import messages

from base.forms import CMSUpgradeForm
from base.models import VersionUpgradeStatus, CHECKPOINTS
from base.utils import get_latest_cms_release, send_upgrade_command


def handler500(request):
    context = {}
    response = render(request, "500.html", context=context)
    response.status_code = 500
    return response


def cms_version_view(request):
    # set upgrade status
    if cache.get("cms_upgrade_pending") is None:
        cache.set("cms_upgrade_pending", False)

    template_name = "admin/cms_version.html"
    current_version = getattr(settings, "CMS_VERSION", None)
    cms_upgrade_hook_url = getattr(settings, "CMS_UPGRADE_HOOK_URL", None)

    try:
        latest_release = get_latest_cms_release()
    except Exception:
        latest_release = {}

    context = {
        "current_version": current_version,
        "cms_upgrade_hook_url": cms_upgrade_hook_url
    }

    if latest_release and current_version:
        latest_version = latest_release.get("version")
        context.update({
            "latest_release": latest_release
        })

        initial = {
            "latest_version": latest_version,
            "current_version": current_version
        }
        form = CMSUpgradeForm(initial=initial)

        context.update({
            "form": form,
        })

    latest_version = latest_release.get("version")
    initial = {
        "latest_version": latest_version,
        "current_version": current_version
    }

    if request.POST:
        form = CMSUpgradeForm(request.POST)

        if form.is_valid() and cms_upgrade_hook_url:
            current_version = form.cleaned_data.get("current_version")
            latest_version = form.cleaned_data.get("latest_version")

            status_data = {
                "previous_version": current_version,
                "new_version": latest_version,
                "checkpoint": "init",
            }

            init_status = VersionUpgradeStatus.objects.filter(**status_data).first()

            if init_status and init_status.success:
                return redirect(reverse("cms-version"))

            try:
                send_upgrade_command(cms_upgrade_hook_url, latest_version)

                if init_status:
                    init_status.success = True
                    init_status.save()
                else:
                    status_data.update({
                        "success": True,
                    })
                    VersionUpgradeStatus.objects.create(**status_data)
                messages.success(request, "CMS upgrade initiated successfully")

            except Exception as e:
                if init_status:
                    init_status.success = False
                    init_status.save()
                else:
                    status_data.update({
                        "success": False,
                    })
                    VersionUpgradeStatus.objects.create(**status_data)

                messages.error(request, "Error initiating CMS upgrade. Please ensure the "
                                        "'CMS_UPGRADE_HOOK_URL' env variable is working correctly")
            return redirect(reverse("cms-version"))
        else:
            context.update({
                "form": form
            })

            return render(request, template_name, context=context)
    else:
        upgrade_form = CMSUpgradeForm(initial=initial)
        db_status = VersionUpgradeStatus.objects.filter(previous_version=current_version, new_version=latest_version)
        should_retry = False

        status_dict = {
            "init": {
                "success": False,
                "prev": None,
                "label": CHECKPOINTS.get("init"),
                "pending": False
            },
            "build": {
                "success": False,
                "pending": False,
                "prev": "init",
                "label": CHECKPOINTS.get("build")
            },
            "env_update": {
                "success": False,
                "pending": False,
                "prev": "build",
                "label": CHECKPOINTS.get("env_update")
            },
            "recreate": {
                "success": False,
                "pending": False,
                "prev": "env_update",
                "label": CHECKPOINTS.get("recreate")
            }
        }

        checkpoints = []

        for state in db_status:
            checkpoints.append(state.checkpoint)
            if status_dict.get(state.checkpoint):
                status_dict[state.checkpoint].update({
                    "success": state.success,
                    "time": state.updated
                })

        for key, value in status_dict.items():

            if key not in checkpoints:
                status_dict[key].update({
                    "pending": True
                })

            prev = value.get("prev")
            if prev and status_dict[prev]:
                status_dict[key].update({
                    "prev_success": status_dict[prev].get("success")
                })

        context.update({
            "form": upgrade_form,
            "should_retry": should_retry,
            "status_dict": status_dict
        })

    return render(request, template_name, context=context)
