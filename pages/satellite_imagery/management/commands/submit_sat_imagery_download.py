from datetime import timedelta

from background_task.models import Task
from django.core.management.base import BaseCommand

from pages.satellite_imagery.tasks import download_imagery


class Command(BaseCommand):
    help = "Submits task to download daily satellite imagery"

    def handle(self, *args, **options):
        tasks = Task.objects.filter(verbose_name="download_imagery")

        if tasks.exists():
            self.stdout.write(
                self.style.SUCCESS("Satellite imagery download task already exists. Submitting Skipped...."))
        else:
            download_imagery(repeat=timedelta(minutes=5).seconds, verbose_name="download_imagery")

            self.stdout.write(self.style.SUCCESS("Successfully submitted satellite imagery download task"))
