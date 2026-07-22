from celery.schedules import crontab
from celery.signals import task_prerun, worker_process_init, worker_ready
from celery_singleton import Singleton, clear_locks
from django.core.management import call_command
from loguru import logger
from opentelemetry import baggage, context

from django.conf import settings

from climweb.config.celery import app
from climweb.config.telemetry.telemetry import setup_telemetry, setup_logging
from climweb.config.telemetry.utils import otel_is_enabled

TASK_NAME_KEY = "celery.task_name"


@worker_process_init.connect
def initialize_otel(**kwargs):
    setup_telemetry(add_django_instrumentation=False)
    setup_logging()


@task_prerun.connect
def before_task(task_id, task, *args, **kwargs):
    if otel_is_enabled():
        context.attach(baggage.set_baggage(TASK_NAME_KEY, task.name))


@worker_ready.connect
def unlock_all(**kwargs):
    # Clear any singleton locks left behind by a previous worker crash.
    # Without this, a task killed mid-run (e.g. by CELERY_WORKER_MAX_MEMORY_PER_CHILD)
    # would leave its Redis lock open and all subsequent scheduled runs would be skipped.
    clear_locks(app)


@app.task(
    base=Singleton,
    bind=True
)
def run_backup(self):
    from django.utils import timezone
    from climweb.base.models.backup_settings import BackupSettings, BackupStatus
    from climweb.base.backups.notify import notify_failure

    # Run the local dump commands. If these fail (e.g. a pg_dump version
    # mismatch), record the failure against every enabled destination so it
    # shows in the CMS panel and triggers a notification — otherwise the failure
    # would only appear in the logs.
    try:
        logger.info("[BACKUP] Running backup")
        call_command('dbbackup', '--clean', '--noinput')
        logger.info("[BACKUP] Running mediabackup")
        call_command('mediabackup', '--clean', '--noinput')
    except Exception as exc:
        logger.exception("[BACKUP] Local backup dump failed")
        message = f"Local backup dump failed: {exc}"
        for backup_settings in BackupSettings.objects.filter(enabled=True):
            if not backup_settings.provider_ready():
                continue
            backup_settings.last_backup_status = BackupStatus.FAILED
            backup_settings.last_backup_message = message
            backup_settings.last_backup_at = timezone.now()
            backup_settings.save(update_fields=[
                "last_backup_at", "last_backup_status", "last_backup_message",
            ])
            notify_failure(backup_settings, message)
        return

    # Upload the fresh dumps to any cloud destinations configured in the CMS admin
    # (Settings -> Backup). Failures here must not fail the local backup.
    try:
        upload_cloud_backups()
    except Exception:
        logger.exception("[BACKUP] Cloud upload step failed")


def upload_cloud_backups():
    """Upload local backups to each site's configured destination (Google Drive
    or a remote server over SFTP), for every site that has enabled and configured
    backups from the CMS admin."""
    import os
    from django.utils import timezone

    from climweb.base.models.backup_settings import BackupSettings, BackupStatus
    from climweb.base.backups.notify import notify_failure

    backup_dir = settings.DBBACKUP_STORAGE_OPTIONS.get("location")
    if not backup_dir or not os.path.isdir(backup_dir):
        logger.warning("[BACKUP] Backup directory not found; skipping cloud upload")
        return

    for backup_settings in BackupSettings.objects.filter(enabled=True):
        if not backup_settings.provider_ready():
            continue

        if backup_settings.provider == "sftp":
            from climweb.base.backups.sftp import upload_backups
        else:
            from climweb.base.backups.google_drive import upload_backups

        try:
            message = upload_backups(backup_settings, backup_dir)
            backup_settings.last_backup_status = BackupStatus.SUCCESS
            backup_settings.last_backup_message = message
            logger.info(f"[BACKUP] Cloud upload complete: {message}")
        except Exception as exc:
            backup_settings.last_backup_status = BackupStatus.FAILED
            backup_settings.last_backup_message = str(exc)
            logger.exception("[BACKUP] Cloud upload failed for a site")
            notify_failure(backup_settings, str(exc))
        finally:
            backup_settings.last_backup_at = timezone.now()
            backup_settings.save(update_fields=[
                "last_backup_at", "last_backup_status", "last_backup_message",
            ])


if "forecastmanager" in settings.INSTALLED_APPS:
    # lock_expiry prevents the singleton lock from persisting indefinitely if the
    # worker is killed (e.g. by CELERY_WORKER_MAX_MEMORY_PER_CHILD) before the
    # task completes and can release the lock normally.  Set to slightly longer
    # than the worst-case runtime so a legitimately-running task is never evicted,
    # but a stuck lock is cleared within a reasonable window.
    _FORECAST_LOCK_EXPIRY = 1800  # 30 minutes

    @app.task(
        base=Singleton,
        bind=True,
        lock_expiry=_FORECAST_LOCK_EXPIRY,
    )
    def download_forecast(self):
        # Run the `generate_forecast` command
        logger.info("[FORECAST] Running generate_forecast")
        try:
            call_command('generate_auto_forecast')
        except Exception as exc:
            logger.error(f"[FORECAST] generate_forecast failed: {exc}")
            raise  # re-raise so Celery records the failure and releases the lock

    @app.task(
        base=Singleton,
        bind=True,
        lock_expiry=_FORECAST_LOCK_EXPIRY,
    )
    def clear_old_forecasts(self):
        # Run the `clear_old_forecasts` command
        logger.info("[FORECAST] Running clear_old_forecasts")
        try:
            call_command('clear_old_forecasts')
        except Exception as exc:
            logger.error(f"[FORECAST] clear_old_forecasts failed: {exc}")
            raise


if "climweb_wdqms" in settings.INSTALLED_APPS:
    @app.task(base=Singleton, bind=True)
    def run_wdqms_stats(self, variable):
        # Log that the task is starting
        logger.info(f"[WDQMS] Running wdqms_stats for {variable}")

        # Run the `wdqms_stats` management command
        call_command('wdqms_stats', '-var', variable)


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    # run_backup every day at midnight
    sender.add_periodic_task(
        crontab(hour=0, minute=0),
        run_backup.s(),
        name="run-backup-every-day-midnight",
    )

    if "forecastmanager" in settings.INSTALLED_APPS:
        # download_forecast every hour
        sender.add_periodic_task(
            crontab(minute=0),
            download_forecast.s(),
            name="download-forecast-every-hour",
        )

        # clear_old_forecasts every day at midnight
        sender.add_periodic_task(
            crontab(hour=0, minute=0),
            clear_old_forecasts.s(),
            name="clear-old-forecasts-every-day-midnight",
        )

    if "climweb_wdqms" in settings.INSTALLED_APPS:
        # Schedule task for pressure at 00:00 and 12:00
        sender.add_periodic_task(
            crontab(hour='0,12', minute=0),
            run_wdqms_stats.s('pressure'),
            name='Run wdqms_stats for pressure at 00:00 and 12:00'
        )

        # Schedule task for temperature at 00:00 and 12:00
        sender.add_periodic_task(
            crontab(hour='0,12', minute=0),
            run_wdqms_stats.s('temperature'),
            name='Run wdqms_stats for temperature at 00:00 and 12:00'
        )

        # Schedule task for humidity at 00:00 and 12:00
        sender.add_periodic_task(
            crontab(hour='0,12', minute=0),
            run_wdqms_stats.s('humidity'),
            name='Run wdqms_stats for humidity at 00:00 and 12:00'
        )

        # Schedule task for meridional_wind at 00:00 and 12:00
        sender.add_periodic_task(
            crontab(hour='0,12', minute=0),
            run_wdqms_stats.s('meridional_wind'),
            name='Run wdqms_stats for meridional_wind at 00:00 and 12:00'
        )

        # Schedule task for zonal_wind at 00:00 and 12:00
        sender.add_periodic_task(
            crontab(hour='0,12', minute=0),
            run_wdqms_stats.s('zonal_wind'),
            name='Run wdqms_stats for zonal_wind at 00:00 and 12:00'
        )
