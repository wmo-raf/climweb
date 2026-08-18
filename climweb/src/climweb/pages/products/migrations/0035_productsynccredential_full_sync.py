from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0034_productsyncsetupcode_productsynccredential'),
    ]

    operations = [
        migrations.AddField(
            model_name='productsynccredential',
            name='full_sync_requested_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Full Sync Requested At'),
        ),
        migrations.AddField(
            model_name='productsynccredential',
            name='full_sync_completed_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Full Sync Completed At'),
        ),
    ]
