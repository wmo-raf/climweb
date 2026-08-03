from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from climweb.base.task_health import queries


class _Schedule:
    """Duck-types the celery schedule object hanging off a PeriodicTask."""

    def __init__(self, remaining=None, raises=False):
        self._remaining = remaining
        self._raises = raises

    def remaining_estimate(self, last_run_at):
        if self._raises:
            raise ValueError("unreadable schedule")
        return self._remaining


class _PeriodicTask:
    def __init__(self, name="a-task", enabled=True, one_off=False,
                 last_run_at="now", remaining=timedelta(minutes=30), raises=False):
        self.name = name
        self.enabled = enabled
        self.one_off = one_off
        self.last_run_at = timezone.now() if last_run_at == "now" else last_run_at
        self.schedule = _Schedule(remaining=remaining, raises=raises)
        self.interval = None
        self.crontab = None
        self.solar = None
        self.clocked = None


class OverdueDetectionTests(SimpleTestCase):
    def test_on_schedule_is_not_overdue(self):
        task = _PeriodicTask(remaining=timedelta(minutes=30))
        self.assertIsNone(queries._overdue_by(task))

    def test_past_due_beyond_the_grace_period_is_overdue(self):
        task = _PeriodicTask(remaining=-timedelta(hours=6))
        overdue = queries._overdue_by(task)
        self.assertEqual(overdue, timedelta(hours=6))

    def test_slightly_late_is_tolerated(self):
        """A task a minute late is not an incident; clocks drift."""
        task = _PeriodicTask(remaining=-timedelta(minutes=1))
        self.assertIsNone(queries._overdue_by(task))

    def test_exactly_at_the_grace_boundary_is_not_flagged(self):
        task = _PeriodicTask(remaining=-queries.OVERDUE_GRACE)
        self.assertIsNone(queries._overdue_by(task))

    def test_disabled_task_is_never_overdue(self):
        task = _PeriodicTask(enabled=False, remaining=-timedelta(days=5))
        self.assertIsNone(queries._overdue_by(task))

    def test_one_off_task_is_never_overdue(self):
        task = _PeriodicTask(one_off=True, remaining=-timedelta(days=5))
        self.assertIsNone(queries._overdue_by(task))

    def test_never_run_task_is_reported_separately_not_as_overdue(self):
        task = _PeriodicTask(last_run_at=None, remaining=-timedelta(days=5))
        self.assertIsNone(queries._overdue_by(task))

    def test_unreadable_schedule_does_not_raise(self):
        """Solar and clocked schedules can blow up in remaining_estimate."""
        task = _PeriodicTask(raises=True)
        self.assertIsNone(queries._overdue_by(task))

    def test_none_remaining_is_handled(self):
        task = _PeriodicTask(remaining=None)
        self.assertIsNone(queries._overdue_by(task))


class ScheduleDescriptionTests(SimpleTestCase):
    def test_prefers_whichever_schedule_type_is_set(self):
        task = _PeriodicTask()
        task.crontab = "0 0 * * * (m/h/dM/MY/d)"
        self.assertIn("0 0", queries._schedule_description(task))

    def test_no_schedule_yields_empty_string(self):
        self.assertEqual(queries._schedule_description(_PeriodicTask()), "")


class TaskHealthViewPermissionTests(TestCase):
    def test_non_superuser_is_refused(self):
        editor = get_user_model().objects.create_user(
            username="editor", password="pw12345!", is_staff=True
        )
        self.client.force_login(editor)

        response = self.client.get(reverse("task-health"))
        self.assertEqual(response.status_code, 403)

    def test_superuser_gets_the_page(self):
        admin = get_user_model().objects.create_superuser(
            username="admin", password="pw12345!", email="a@example.com"
        )
        self.client.force_login(admin)

        response = self.client.get(reverse("task-health"))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["error"])


class TaskHealthDataTests(TestCase):
    """Exercised against the real django_celery_* tables."""

    def setUp(self):
        from django_celery_results.models import TaskResult

        self.TaskResult = TaskResult

    def _result(self, status="SUCCESS", name="climweb.base.tasks.run_backup",
                traceback="", age=timedelta(minutes=5)):
        created = timezone.now() - age
        return self.TaskResult.objects.create(
            task_id=f"{name}-{status}-{timezone.now().timestamp()}",
            task_name=name,
            status=status,
            traceback=traceback,
            date_created=created,
            date_done=created + timedelta(seconds=2),
            worker="default-worker@climweb",
        )

    def test_summary_counts_failures_and_successes(self):
        self._result(status="SUCCESS")
        self._result(status="SUCCESS")
        self._result(status="FAILURE")

        result = queries.summary(window_hours=24)
        self.assertEqual(result["succeeded"], 2)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(result["total"], 3)
        self.assertEqual(result["worker_state"], "active")

    def test_summary_reports_a_silent_worker(self):
        """The signal that celery is down, rather than merely idle."""
        self._result(age=timedelta(days=3))

        result = queries.summary(window_hours=24)
        self.assertEqual(result["worker_state"], "silent")
        # Outside the window, so it isn't counted, but liveness still uses it.
        self.assertEqual(result["total"], 0)

    def test_summary_with_no_results_at_all(self):
        result = queries.summary()
        self.assertEqual(result["worker_state"], "unknown")
        self.assertIsNone(result["last_result_at"])

    def test_recent_results_can_filter_to_failures(self):
        self._result(status="SUCCESS")
        self._result(status="FAILURE")

        self.assertEqual(len(queries.recent_results()), 2)
        failures = queries.recent_results(only_failures=True)
        self.assertEqual(len(failures), 1)
        self.assertTrue(failures[0]["is_failure"])

    def test_recent_results_redacts_tracebacks(self):
        self._result(
            status="FAILURE",
            traceback="OperationalError: password authentication failed for leaked-pw-value",
        )

        env = {"CMS_DB_PASSWORD": "leaked-pw-value"}
        with mock.patch.dict("os.environ", env, clear=True):
            results = queries.recent_results(only_failures=True)

        self.assertNotIn("leaked-pw-value", results[0]["traceback"])

    def test_recent_results_filters_by_task_name(self):
        self._result(name="climweb.base.tasks.run_backup")
        self._result(name="climweb.base.tasks.download_forecast")

        matched = queries.recent_results(task_name="download_forecast")
        self.assertEqual(len(matched), 1)
        self.assertIn("download_forecast", matched[0]["task_name"])

    def test_beat_housekeeping_entry_is_hidden(self):
        """celery.backend_cleanup tells an operator nothing about ClimWeb."""
        from django_celery_beat.models import CrontabSchedule, PeriodicTask

        schedule = CrontabSchedule.objects.create(hour="0", minute="0")
        PeriodicTask.objects.create(
            name="celery.backend_cleanup",
            task="celery.backend_cleanup",
            crontab=schedule,
        )
        PeriodicTask.objects.create(
            name="run-backup-every-day-midnight",
            task="climweb.base.tasks.run_backup",
            crontab=schedule,
        )

        names = [row["name"] for row in queries.scheduled_tasks()]
        self.assertNotIn("celery.backend_cleanup", names)
        self.assertIn("run-backup-every-day-midnight", names)

    def test_scheduled_tasks_sort_problems_first(self):
        from django_celery_beat.models import CrontabSchedule, PeriodicTask

        schedule = CrontabSchedule.objects.create(hour="0", minute="0")
        PeriodicTask.objects.create(
            name="healthy", task="a", crontab=schedule,
            last_run_at=timezone.now(),
        )
        PeriodicTask.objects.create(name="never-run", task="b", crontab=schedule)

        rows = queries.scheduled_tasks()
        self.assertEqual(rows[0]["name"], "never-run")
        self.assertTrue(rows[0]["never_run"])
