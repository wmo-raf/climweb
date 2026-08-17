"""Read background-task health out of the database.

Everything here comes from data ClimWeb already stores: `CELERY_RESULT_BACKEND`
is "django-db", so every task outcome lands in django_celery_results, and
`CELERY_BEAT_SCHEDULER` is the DatabaseScheduler, so the periodic tasks declared
in base/tasks.py are synced into django_celery_beat as rows.

The questions this is meant to answer without an SSH session:

* did last night's backup actually run?
* is the hourly forecast download failing, and with what error?
* is the worker alive at all?
"""

import logging
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from climweb.base.logs.docker_client import redact

logger = logging.getLogger(__name__)

FAILURE_STATES = ("FAILURE", "REVOKED", "REJECTED")
IN_FLIGHT_STATES = ("STARTED", "RETRY", "PENDING", "RECEIVED")

DEFAULT_WINDOW_HOURS = 24

# A schedule is only called overdue once it is this far past due, so a task that
# is merely a few seconds late (or a clock that drifted) doesn't raise an alarm.
OVERDUE_GRACE = timedelta(minutes=15)

# If nothing at all has been recorded for this long, the worker is probably down
# rather than merely idle — beat alone would still be producing results.
WORKER_SILENT_AFTER = timedelta(hours=25)


def _models():
    """Imported lazily so this module can be imported without app loading."""
    from django_celery_beat.models import PeriodicTask
    from django_celery_results.models import TaskResult

    return PeriodicTask, TaskResult


def summary(window_hours=DEFAULT_WINDOW_HOURS):
    """Counts by status over the window, plus a liveness verdict."""
    _, TaskResult = _models()
    since = timezone.now() - timedelta(hours=window_hours)

    counts = {
        row["status"]: row["n"]
        for row in TaskResult.objects.filter(date_created__gte=since)
        .values("status")
        .annotate(n=Count("id"))
    }

    latest = TaskResult.objects.order_by("-date_done").first()
    last_result_at = latest.date_done if latest else None

    if last_result_at is None:
        worker_state = "unknown"
    elif timezone.now() - last_result_at > WORKER_SILENT_AFTER:
        worker_state = "silent"
    else:
        worker_state = "active"

    return {
        "window_hours": window_hours,
        "succeeded": counts.get("SUCCESS", 0),
        "failed": sum(counts.get(state, 0) for state in FAILURE_STATES),
        "in_flight": sum(counts.get(state, 0) for state in IN_FLIGHT_STATES),
        "total": sum(counts.values()),
        "last_result_at": last_result_at,
        "last_worker": latest.worker if latest else "",
        "worker_state": worker_state,
    }


def _schedule_description(periodic_task):
    for attr in ("interval", "crontab", "solar", "clocked"):
        value = getattr(periodic_task, attr, None)
        if value is not None:
            return str(value)
    return ""


def _overdue_by(periodic_task, now=None):
    """How far past due this schedule is, or None if it isn't.

    Returns a timedelta. Celery's `remaining_estimate` gives time until the next
    run relative to the last one; once negative, the task should already have
    fired.
    """
    now = now or timezone.now()

    if not periodic_task.enabled or periodic_task.one_off:
        return None
    if periodic_task.last_run_at is None:
        # Never run. Only interesting once the schedule has had a chance to fire.
        return None

    try:
        remaining = periodic_task.schedule.remaining_estimate(
            periodic_task.last_run_at
        )
    except Exception:
        # Solar and clocked schedules, or a malformed crontab, can raise here.
        # An unreadable schedule is not a failure worth alarming about.
        logger.debug(
            "[TASK-HEALTH] Could not estimate schedule for %s", periodic_task.name,
            exc_info=True,
        )
        return None

    if remaining is None:
        return None

    overdue = -remaining
    return overdue if overdue > OVERDUE_GRACE else None


def scheduled_tasks():
    """Every periodic task, newest problems first."""
    PeriodicTask, TaskResult = _models()

    rows = []
    for periodic_task in PeriodicTask.objects.all():
        # celery.backend_cleanup is beat's own housekeeping entry; it tells an
        # operator nothing about whether ClimWeb is working.
        if periodic_task.name == "celery.backend_cleanup":
            continue

        overdue = _overdue_by(periodic_task)

        last_result = (
            TaskResult.objects.filter(periodic_task_name=periodic_task.name)
            .order_by("-date_done")
            .first()
        )

        rows.append({
            "name": periodic_task.name,
            "task": periodic_task.task,
            "enabled": periodic_task.enabled,
            "schedule": _schedule_description(periodic_task),
            "last_run_at": periodic_task.last_run_at,
            "total_run_count": periodic_task.total_run_count,
            "overdue_by": overdue,
            "never_run": periodic_task.last_run_at is None,
            "last_status": last_result.status if last_result else "",
        })

    def sort_key(row):
        # Problems first: overdue, then never-run, then everything else.
        return (
            row["overdue_by"] is None,
            not row["never_run"],
            row["name"],
        )

    rows.sort(key=sort_key)
    return rows


def recent_results(window_hours=DEFAULT_WINDOW_HOURS, only_failures=False,
                   task_name="", limit=100):
    """Recent task outcomes, with tracebacks redacted."""
    _, TaskResult = _models()

    since = timezone.now() - timedelta(hours=window_hours)
    queryset = TaskResult.objects.filter(date_created__gte=since)

    if only_failures:
        queryset = queryset.filter(status__in=FAILURE_STATES)
    if task_name:
        queryset = queryset.filter(task_name__icontains=task_name)

    results = []
    for result in queryset.order_by("-date_created")[:limit]:
        duration = None
        if result.date_done and result.date_created:
            duration = (result.date_done - result.date_created).total_seconds()

        results.append({
            "task_name": result.task_name or "",
            "periodic_task_name": result.periodic_task_name or "",
            "status": result.status,
            "date_created": result.date_created,
            "date_done": result.date_done,
            "duration_seconds": duration,
            "worker": result.worker or "",
            # Tracebacks routinely carry connection strings and API responses.
            "traceback": redact(result.traceback or ""),
            "is_failure": result.status in FAILURE_STATES,
        })

    return results


def task_name_choices(window_hours=DEFAULT_WINDOW_HOURS):
    _, TaskResult = _models()
    since = timezone.now() - timedelta(hours=window_hours)
    return sorted(
        name
        for name in TaskResult.objects.filter(date_created__gte=since)
        .values_list("task_name", flat=True)
        .distinct()
        if name
    )
