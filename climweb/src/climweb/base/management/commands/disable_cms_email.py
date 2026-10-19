from django.core.management.base import BaseCommand

from climweb.base.models.email_settings import EmailSettings


class Command(BaseCommand):
    help = (
        "Switch off the email settings managed in the CMS (Settings -> Email), "
        "so the site sends email with the server's EMAIL_* settings again. "
        "The CMS values are kept and can be switched back on from the CMS."
    )

    def handle(self, *args, **options):
        email_settings = EmailSettings.load()

        if not email_settings.enabled:
            self.stdout.write("CMS email settings are already off; the server's settings are in use.")
            return

        email_settings.enabled = False
        email_settings.save(update_fields=["enabled"])

        self.stdout.write(self.style.SUCCESS(
            "CMS email settings switched off. The site now sends email with the server's settings."
        ))
