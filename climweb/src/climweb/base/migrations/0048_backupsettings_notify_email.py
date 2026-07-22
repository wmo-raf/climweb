from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0047_backupsettings_sftp"),
    ]

    operations = [
        migrations.AddField(
            model_name="backupsettings",
            name="notify_email",
            field=models.EmailField(blank=True, help_text="Where to email if a backup fails. Leave blank to use the server's admin addresses.", max_length=254, verbose_name="Failure notification email"),
        ),
    ]
