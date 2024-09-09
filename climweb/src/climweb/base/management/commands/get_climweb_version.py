from climweb.utils.version import get_complete_version, get_semver_version
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Get ClimWeb version"

    def handle(self, *args, **options):
        complete_version = get_complete_version()
        version = get_semver_version(complete_version)
        self.stdout.write(version)
