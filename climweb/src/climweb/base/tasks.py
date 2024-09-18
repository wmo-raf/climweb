from celery.schedules import crontab
from celery_singleton import Singleton
from django.core.management import call_command

from climweb.config.celery import app


@app.task(
    base=Singleton,
    bind=True
)
def run_backup(self):
    # Run the `dbbackup` command
    call_command('dbbackup', '--clean', '--noinput')

    # Run the `mediabackup` command
    call_command('mediabackup', '--clean', '--noinput')


@app.task(
    base=Singleton,
    bind=True
)
def download_forecast(self):
    # Run the `generate_forecast` command
    call_command('generate_forecast')


@app.task(
    base=Singleton,
    bind=True
)
def clear_old_forecasts(self):
    # Run the `clear_old_forecasts` command
    call_command('clear_old_forecasts')


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    # run_backup every day at midnight
    sender.add_periodic_task(
        crontab(hour=0, minute=0),
        run_backup.s(),
        name="run-backup-every-day-midnight",
    )

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
