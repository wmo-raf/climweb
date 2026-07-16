import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0001_initial"),
        ("base", "0044_organisationsetting_logo_append"),
    ]

    operations = [
        migrations.CreateModel(
            name="BackupSettings",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("enabled", models.BooleanField(default=False, help_text="When enabled, the daily backup will be uploaded to the connected cloud account. You must connect an account below first.", verbose_name="Enable cloud backups")),
                ("provider", models.CharField(choices=[("gdrive", "Google Drive")], default="gdrive", max_length=20, verbose_name="Provider")),
                ("remote_folder", models.CharField(default="ClimWeb Backups", help_text="Top-level folder created in the drive to hold backups.", max_length=255, verbose_name="Remote folder")),
                ("db_retention_days", models.PositiveIntegerField(default=10, help_text="Number of daily database snapshots to retain on the remote.", verbose_name="Database copies to keep")),
                ("media_retention_days", models.PositiveIntegerField(default=3, help_text="Number of weekly media snapshots to retain on the remote.", verbose_name="Media copies to keep")),
                ("media_upload_weekday", models.PositiveIntegerField(choices=[(0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"), (4, "Friday"), (5, "Saturday"), (6, "Sunday")], default=0, help_text="Day of the week the (larger) media archive is uploaded.", verbose_name="Media upload day")),
                ("google_account_email", models.CharField(blank=True, editable=False, max_length=254, verbose_name="Connected account")),
                ("encrypted_token", models.TextField(blank=True, editable=False, help_text="Encrypted OAuth refresh token. Never edit by hand.")),
                ("last_backup_at", models.DateTimeField(blank=True, editable=False, null=True)),
                ("last_backup_status", models.CharField(choices=[("never", "Never run"), ("success", "Success"), ("failed", "Failed")], default="never", editable=False, max_length=20)),
                ("last_backup_message", models.TextField(blank=True, editable=False)),
                ("site", models.OneToOneField(db_index=True, editable=False, on_delete=django.db.models.deletion.CASCADE, to="wagtailcore.site", unique=True)),
            ],
            options={
                "verbose_name": "Backup Settings",
                "abstract": False,
            },
        ),
    ]
