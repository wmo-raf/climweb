from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from base.models.upgrade import VersionUpgradeStatus

CMS_VERSION = getattr(settings, "CMS_VERSION", None)


class Command(BaseCommand):
    help = "Update CMS Upgrade Status"

    def add_arguments(self, parser):
        parser.add_argument('previous_version', type=str, help='Previous version as a string')
        parser.add_argument('new_version', type=str, help='New version as a string')
        parser.add_argument('checkpoint', type=str, help='Checkpoint as a string')
        parser.add_argument('--success', action="store_true", default=False, help='Success as a boolean')

    def handle(self, *args, **options):
        previous_version = options['previous_version']
        new_version = options['new_version']
        checkpoint = options['checkpoint']
        success = options['success']

        try:
            if not CMS_VERSION:
                raise ValidationError("Can not get CMS_VERSION from env")

            data = {
                "previous_version": previous_version,
                "new_version": new_version,
                "checkpoint": checkpoint,
            }

            obj, created = VersionUpgradeStatus.objects.get_or_create(**data)
            obj.success = success
            obj.save()

            self.stdout.write(self.style.SUCCESS(
                f'Successfully executed command with previous_version={previous_version}, new_version={new_version}, '
                f'checkpoint={checkpoint}, success={success}'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error: {e}'))
