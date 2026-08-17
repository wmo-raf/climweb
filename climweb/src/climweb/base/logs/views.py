"""Superuser-only container log viewer for the CMS admin.

Replaces having to SSH in and run `docker compose logs -f --tail 100 climweb`.

The page polls a small JSON endpoint rather than holding a streaming connection
open: gunicorn workers are a scarce resource on these instances, and a handful of
editors leaving a `follow` stream open in a forgotten tab would starve the site.
"""

import logging
from datetime import datetime, timezone

from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET

from .docker_client import (
    LogViewerError,
    fetch_logs,
    fetch_logs_text,
    is_enabled,
    list_containers,
)

logger = logging.getLogger(__name__)

DEFAULT_TAIL = 200
TAIL_CHOICES = (100, 200, 500, 1000, 2000)


def _forbidden(request):
    """Logs routinely contain data no ordinary editor should see."""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return HttpResponseForbidden("Superuser access required to view server logs.")
    return None


@require_GET
def log_viewer(request):
    denied = _forbidden(request)
    if denied:
        return denied

    context = {
        "enabled": is_enabled(),
        "containers": [],
        "error": None,
        "default_tail": DEFAULT_TAIL,
        "tail_choices": TAIL_CHOICES,
        "selected": request.GET.get("container") or "",
    }

    if context["enabled"]:
        try:
            context["containers"] = list_containers()
        except LogViewerError as exc:
            context["error"] = str(exc)
        except Exception as exc:
            logger.exception("[LOGS] Unexpected error listing containers")
            context["error"] = str(exc)

    if not context["selected"] and context["containers"]:
        context["selected"] = context["containers"][0]["name"]

    return render(request, "admin/log_viewer.html", context)


@require_GET
def log_fetch(request):
    """JSON tail, polled by the viewer page."""
    denied = _forbidden(request)
    if denied:
        return denied

    container = request.GET.get("container", "")
    since = request.GET.get("since") or None
    try:
        tail = int(request.GET.get("tail", DEFAULT_TAIL))
    except (TypeError, ValueError):
        tail = DEFAULT_TAIL

    try:
        lines = fetch_logs(container, tail=tail, since=since)
    except LogViewerError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception as exc:
        logger.exception("[LOGS] Unexpected error reading logs for %s", container)
        return JsonResponse({"error": str(exc)}, status=500)

    # Docker's `since` filter only resolves to the second, so hand back anything
    # strictly newer than what the client already has. RFC3339 sorts as a string.
    if since:
        lines = [line for line in lines if line["ts"] > since]

    return JsonResponse({
        "lines": lines,
        "latest": lines[-1]["ts"] if lines else since or "",
    })


@require_GET
def log_download(request):
    denied = _forbidden(request)
    if denied:
        return denied

    container = request.GET.get("container", "")
    try:
        tail = int(request.GET.get("tail", 1000))
    except (TypeError, ValueError):
        tail = 1000

    try:
        text = fetch_logs_text(container, tail=min(tail, 5000))
    except LogViewerError as exc:
        return HttpResponse(_("Could not read logs: %s") % exc, status=400)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    response = HttpResponse(text, content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = (
        f'attachment; filename="{container}-logs-{stamp}.txt"'
    )
    return response
