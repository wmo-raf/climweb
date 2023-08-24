from datetime import timedelta
import os
from datetime import datetime, timedelta
from django.core import management
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Perform daily backup and cleanup'

    def handle(self, *args, **options):

        self.stdout.write(self.style.SUCCESS("Starting daily backup and cleanup..."))

        backup_dir = './dump'
        max_backup_age_days = 7

        # Perform backup
        backup_date = datetime.now()
        output_file = os.path.join(backup_dir, f'daily_backup_{backup_date.date()}.json')
        management.call_command('dumpdata', '--output', output_file)
        self.stdout.write(self.style.SUCCESS(f'Successfully backed up all data to {output_file}'))

        # Cleanup old backups
        oldest_allowed_date = datetime.now() - timedelta(days=max_backup_age_days)
        for file_name in os.listdir(backup_dir):
            if file_name.startswith('daily_backup_') and file_name.endswith('.json'):
                file_date_str = file_name.split('_')[2].split('.')[0]
                file_date = datetime.strptime(file_date_str, '%Y-%m-%d')
                if file_date < oldest_allowed_date:
                    file_path = os.path.join(backup_dir, file_name)
                    os.remove(file_path)
                    self.stdout.write(self.style.SUCCESS(f'Removed old backup: {file_path}'))

        self.stdout.write(self.style.SUCCESS("Daily backup and cleanup completed."))
