from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Resets ClimWeb Upgrade Status"

    def handle(self, *args, **options):
        cache.set("cms_upgrade_pending", False)

        self.stdout.write(
            self.style.SUCCESS('Successfully reset ClimWeb Upgrade status')
        )
