"""Background task health page for the CMS admin.

Replaces `docker compose logs climweb_celery_worker` for the two questions that
actually get asked: did the scheduled job run, and if it failed, why.
"""

import logging

from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .queries import (
    DEFAULT_WINDOW_HOURS,
    recent_results,
    scheduled_tasks,
    summary,
    task_name_choices,
)

logger = logging.getLogger(__name__)

WINDOW_CHOICES = (1, 6, 24, 72, 168)


@require_GET
def task_health(request):
    # Tracebacks can contain request data and credentials, same as the server
    # logs, so this stays superuser-only.
    if not request.user.is_authenticated or not request.user.is_superuser:
        return HttpResponseForbidden(
            "Superuser access required to view background task health."
        )

    try:
        window_hours = int(request.GET.get("window", DEFAULT_WINDOW_HOURS))
    except (TypeError, ValueError):
        window_hours = DEFAULT_WINDOW_HOURS
    if window_hours not in WINDOW_CHOICES:
        window_hours = DEFAULT_WINDOW_HOURS

    only_failures = request.GET.get("failures") == "1"
    task_name = (request.GET.get("task") or "").strip()

    context = {
        "window_hours": window_hours,
        "window_choices": WINDOW_CHOICES,
        "only_failures": only_failures,
        "task_name": task_name,
        "error": None,
        "summary": None,
        "scheduled": [],
        "results": [],
        "task_names": [],
    }

    try:
        context["summary"] = summary(window_hours=window_hours)
        context["scheduled"] = scheduled_tasks()
        context["results"] = recent_results(
            window_hours=window_hours,
            only_failures=only_failures,
            task_name=task_name,
        )
        context["task_names"] = task_name_choices(window_hours=window_hours)
    except Exception as exc:
        logger.exception("[TASK-HEALTH] Could not read task health")
        context["error"] = str(exc)

    return render(request, "admin/task_health.html", context)
