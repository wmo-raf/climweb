from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0045_backupsettings"),
    ]

    operations = [
        migrations.AddField(
            model_name="backupsettings",
            name="oauth_client_id",
            field=models.CharField(blank=True, help_text="From your Google Cloud OAuth 'Web application' client. This value is public. Required for the Connect button.", max_length=255, verbose_name="OAuth Client ID"),
        ),
        migrations.AddField(
            model_name="backupsettings",
            name="oauth_client_secret",
            field=models.CharField(blank=True, max_length=512, verbose_name="OAuth Client Secret"),
        ),
        migrations.AddField(
            model_name="backupsettings",
            name="paste_refresh_token",
            field=models.CharField(blank=True, max_length=4096, verbose_name="Paste a token (fallback)"),
        ),
    ]
