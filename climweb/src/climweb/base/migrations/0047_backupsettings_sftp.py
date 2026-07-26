from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0046_backupsettings_oauth_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="backupsettings",
            name="sftp_host",
            field=models.CharField(blank=True, help_text="Destination server hostname or IP.", max_length=255, verbose_name="Host"),
        ),
        migrations.AddField(
            model_name="backupsettings",
            name="sftp_port",
            field=models.PositiveIntegerField(default=22, verbose_name="Port"),
        ),
        migrations.AddField(
            model_name="backupsettings",
            name="sftp_username",
            field=models.CharField(blank=True, max_length=255, verbose_name="Username"),
        ),
        migrations.AddField(
            model_name="backupsettings",
            name="sftp_remote_path",
            field=models.CharField(default="climweb-backups", help_text="Directory on the destination server (relative to the login home, or an absolute path). Created if missing.", max_length=512, verbose_name="Remote directory"),
        ),
        migrations.AddField(
            model_name="backupsettings",
            name="sftp_auth_method",
            field=models.CharField(choices=[("key", "SSH key (recommended)"), ("password", "Password")], default="key", max_length=10, verbose_name="Authentication"),
        ),
        migrations.AddField(
            model_name="backupsettings",
            name="sftp_password",
            field=models.CharField(blank=True, max_length=512, verbose_name="Password"),
        ),
        migrations.AddField(
            model_name="backupsettings",
            name="sftp_private_key",
            field=models.TextField(blank=True, editable=False),
        ),
        migrations.AddField(
            model_name="backupsettings",
            name="paste_private_key",
            field=models.TextField(blank=True, verbose_name="Paste an SSH private key (fallback)"),
        ),
        migrations.AddField(
            model_name="backupsettings",
            name="sftp_public_key",
            field=models.TextField(blank=True, editable=False),
        ),
        migrations.AddField(
            model_name="backupsettings",
            name="sftp_host_key",
            field=models.TextField(blank=True, editable=False),
        ),
    ]
